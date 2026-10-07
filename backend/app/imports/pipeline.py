from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.phone import normalize
from app.imports.schemas import CommitResult, Conflict, Issue, Preview, PreviewRow
from app.invitations import service
from app.invitations.models import Invitation, InvitationContact
from app.invitations.schemas import ContactIn, InvitationIn, MemberIn


def row_to_draft(row: list[str], mapping: list[str]) -> InvitationIn | None:
    """One spreadsheet row -> one InvitationIn. Phone N attaches to Person N. None if no name."""
    name = group = note = ""
    persons: dict[int, str] = {}
    phones: dict[int, str] = {}
    for cell, target in zip(row, mapping):
        cell = cell.strip()
        if not cell:
            continue
        kind, _, n = target.partition(":")
        if kind == "invitation_name":
            name = cell
        elif kind == "group":
            group = cell
        elif kind == "note":
            note = cell
        elif kind == "person":
            persons[int(n)] = cell
        elif kind == "phone":
            phones[int(n)] = cell
    order = sorted(persons)
    members = [MemberIn(name=persons[n]) for n in order]
    contacts = [ContactIn(phone=phones[n], member_index=order.index(n) if n in persons else None) for n in sorted(phones)]
    return InvitationIn(display_name=name or " ", group_name=group or None, notes=note or None,
                        members=members, contacts=contacts) if name else None


def build_preview(db: Session, event_id: int, rows: list[list[str]], mapping: list[str]) -> Preview:
    existing_by_phone: dict[str, Conflict] = {}
    for e164, inv_id, inv_name in db.execute(
        select(InvitationContact.phone_e164, Invitation.id, Invitation.display_name)
        .join(Invitation).where(Invitation.event_id == event_id, InvitationContact.phone_e164.is_not(None))
    ):
        existing_by_phone.setdefault(e164, Conflict(invitation_id=inv_id, invitation_name=inv_name))
    existing_by_name: dict[str, Conflict] = {}
    for inv_id, inv_name in db.execute(select(Invitation.id, Invitation.display_name).where(Invitation.event_id == event_id)):
        existing_by_name.setdefault(inv_name.lower(), Conflict(invitation_id=inv_id, invitation_name=inv_name))

    seen_phones: set[str] = set()
    seen_rows: set[tuple] = set()
    out: list[PreviewRow] = []
    for idx, row in enumerate(rows):
        draft = row_to_draft(row, mapping)
        issues: list[Issue] = []
        conflict = None
        default = "new"
        if draft is None:
            issues.append(Issue(code="missing_name", level="error"))
            default = "skip"
        else:
            e164s = []
            for c in draft.contacts:
                e164 = normalize(c.phone)
                if e164 is None:
                    issues.append(Issue(code="invalid_phone", level="warning", detail=c.phone))
                    continue
                e164s.append(e164)
                if e164 in seen_phones:
                    issues.append(Issue(code="duplicate_phone_in_file", level="warning", detail=e164))
                if e164 in existing_by_phone and not conflict:
                    conflict = existing_by_phone[e164]
                    issues.append(Issue(code="existing_phone", level="conflict", detail=e164))
            if (conflict is None) and draft.display_name.lower() in existing_by_name:
                conflict = existing_by_name[draft.display_name.lower()]
                issues.append(Issue(code="existing_name", level="conflict", detail=draft.display_name))
            key = (draft.display_name.lower(), tuple(sorted(e164s)))
            if key in seen_rows:
                issues.append(Issue(code="duplicate_row", level="warning"))
                default = "skip"
            seen_rows.add(key)
            seen_phones.update(e164s)
            if conflict:
                default = "skip"
        levels = {i.level for i in issues}
        status = "error" if "error" in levels else "conflict" if "conflict" in levels else "warning" if issues else "ok"
        out.append(PreviewRow(index=idx, draft=draft, status=status, issues=issues, conflict=conflict, default_action=default))
    counts = {s: sum(r.status == s for r in out) for s in ("ok", "warning", "conflict", "error")}
    return Preview(rows=out, counts=counts)


def commit(db: Session, event_id: int, rows, mapping, actions) -> CommitResult:
    """Applies the preview with the admin's chosen actions in one transaction. Errors are never imported."""
    preview = build_preview(db, event_id, rows, mapping)
    created = updated = skipped = 0
    for r in preview.rows:
        action = actions.get(r.index, r.default_action)
        if r.status == "error" or r.draft is None or action == "skip":
            skipped += 1
        elif action == "update" and r.conflict:
            service.apply_input(db, db.get(Invitation, r.conflict.invitation_id), r.draft)
            updated += 1
        else:
            service.create_invitation(db, event_id, r.draft)
            created += 1
    db.commit()
    return CommitResult(created=created, updated=updated, skipped=skipped)
