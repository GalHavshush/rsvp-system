from sqlalchemy import exists, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.phone import normalize
from app.invitations.models import Group, Invitation, InvitationContact, InvitationMember
from app.invitations.schemas import InvitationIn


def get_or_create_group(db: Session, event_id: int, name: str | None) -> Group | None:
    name = (name or "").strip()
    if not name:
        return None
    group = db.scalar(select(Group).where(Group.event_id == event_id, func.lower(Group.name) == name.lower()))
    if not group:
        group = Group(event_id=event_id, name=name)
        db.add(group)
        db.flush()
    return group


def apply_input(db: Session, inv: Invitation, data: InvitationIn) -> None:
    """Set fields and replace members/contacts from `data` (RSVP state is untouched)."""
    inv.display_name = data.display_name.strip()
    inv.notes = data.notes
    group = get_or_create_group(db, inv.event_id, data.group_name)
    inv.group_id = group.id if group else None
    inv.members.clear()
    inv.contacts.clear()
    db.flush()
    members = [InvitationMember(name=m.name.strip(), position=i) for i, m in enumerate(data.members)]
    inv.members.extend(members)
    db.flush()
    for i, c in enumerate(data.contacts):
        e164 = normalize(c.phone)
        inv.contacts.append(InvitationContact(
            member_id=members[c.member_index].id if c.member_index is not None else None,
            phone_raw=c.phone.strip(), phone_e164=e164, phone_valid=e164 is not None, position=i))


def create_invitation(db: Session, event_id: int, data: InvitationIn) -> Invitation:
    inv = Invitation(event_id=event_id, display_name=data.display_name)
    db.add(inv)
    apply_input(db, inv, data)
    return inv


def list_query(event_id: int, *, q=None, rsvp_status=None, group_id=None, missing_phone=False,
               invalid_phone=False, message_state=None):
    stmt = select(Invitation).where(Invitation.event_id == event_id)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(
            Invitation.display_name.ilike(like),
            exists().where(InvitationMember.invitation_id == Invitation.id, InvitationMember.name.ilike(like)),
            exists().where(InvitationContact.invitation_id == Invitation.id,
                           or_(InvitationContact.phone_raw.ilike(like), InvitationContact.phone_e164.ilike(like))),
        ))
    if rsvp_status:
        stmt = stmt.where(Invitation.rsvp_status == rsvp_status)
    if group_id:
        stmt = stmt.where(Invitation.group_id == group_id)
    if missing_phone:
        stmt = stmt.where(~exists().where(InvitationContact.invitation_id == Invitation.id))
    if invalid_phone:
        stmt = stmt.where(exists().where(InvitationContact.invitation_id == Invitation.id,
                                         InvitationContact.phone_valid.is_(False)))
    if message_state:
        stmt = stmt.where(Invitation.message_state == message_state)
    return stmt


SORTS = {
    "name": Invitation.display_name.asc(), "-name": Invitation.display_name.desc(),
    "updated": Invitation.rsvp_updated_at.asc().nulls_last(), "-updated": Invitation.rsvp_updated_at.desc().nulls_last(),
    "status": Invitation.rsvp_status.asc(),
}


def fetch_page(db: Session, stmt, sort: str, limit: int, offset: int):
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(
        stmt.options(selectinload(Invitation.members), selectinload(Invitation.contacts), joinedload(Invitation.group))
        .order_by(SORTS[sort], Invitation.id).limit(limit).offset(offset)
    ).all()
    return rows, total


def export_rows(invitations: list[Invitation], labels: dict[str, str]) -> list[list[object]]:
    """Spreadsheet representation (Person N / Phone N columns); same shape the importer reads."""
    slots_per_inv = []
    for inv in invitations:
        by_member = {c.member_id: c for c in inv.contacts if c.member_id}
        slots = [(m.name, by_member[m.id].phone_raw if m.id in by_member else "") for m in inv.members]
        slots += [("", c.phone_raw) for c in inv.contacts if not c.member_id]
        slots_per_inv.append(slots)
    width = max((len(s) for s in slots_per_inv), default=0)
    header = [labels["invitation_name"], labels["group"], labels["status"], labels["attendees"], labels["notes"]]
    for i in range(1, width + 1):
        header += [f"{labels['person']} {i}", f"{labels['phone']} {i}"]
    rows: list[list[object]] = [header]
    for inv, slots in zip(invitations, slots_per_inv):
        row = [inv.display_name, inv.group_name or "", labels.get(inv.rsvp_status, inv.rsvp_status),
               inv.attendee_count if inv.attendee_count is not None else "", inv.notes or ""]
        for name, phone in slots:
            row += [name, phone]
        rows.append(row + [""] * (len(header) - len(row)))
    return rows
