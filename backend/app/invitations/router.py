from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import current_admin
from app.core.csvutil import to_csv_bytes
from app.core.db import get_db
from app.events.router import get_event
from app.invitations import service
from app.invitations.models import Group, Invitation
from app.invitations.schemas import GroupIn, GroupOut, InvitationIn, InvitationOut, InvitationPage, RsvpStatus

router = APIRouter(prefix="/api", dependencies=[Depends(current_admin)])

LABELS = {
    "he": {"invitation_name": "שם הזמנה", "group": "קבוצה", "status": "סטטוס", "attendees": "מגיעים", "notes": "הערות",
           "person": "שם", "phone": "טלפון", "no_response": "לא ענו", "coming": "מגיעים", "not_coming": "לא מגיעים", "maybe": "אולי"},
    "en": {"invitation_name": "Invitation Name", "group": "Group", "status": "Status", "attendees": "Attendees", "notes": "Notes",
           "person": "Person", "phone": "Phone", "no_response": "No response", "coming": "Coming", "not_coming": "Not coming", "maybe": "Maybe"},
}


def _inv(db: Session, invitation_id: int) -> Invitation:
    inv = db.get(Invitation, invitation_id)
    if not inv:
        raise HTTPException(404, "invitation_not_found")
    return inv


def _filters(q: str | None = None, rsvp_status: RsvpStatus | None = None, group_id: int | None = None,
             missing_phone: bool = False, invalid_phone: bool = False, message_state: str | None = None):
    return dict(q=q, rsvp_status=rsvp_status, group_id=group_id, missing_phone=missing_phone,
                invalid_phone=invalid_phone, message_state=message_state)


@router.get("/events/{event_id}/invitations", response_model=InvitationPage)
def list_invitations(event_id: int, f: dict = Depends(_filters),
                     sort: Literal["name", "-name", "updated", "-updated", "status"] = "name",
                     limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    get_event(db, event_id)
    items, total = service.fetch_page(db, service.list_query(event_id, **f), sort, limit, offset)
    return InvitationPage(items=items, total=total)


@router.get("/events/{event_id}/invitations/export")
def export_invitations(event_id: int, lang: Literal["he", "en"] = "he", f: dict = Depends(_filters),
                       db: Session = Depends(get_db)):
    get_event(db, event_id)
    items, _ = service.fetch_page(db, service.list_query(event_id, **f), "name", 100000, 0)
    body = to_csv_bytes(service.export_rows(items, LABELS[lang]))
    return Response(body, media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="invitations.csv"'})


@router.post("/events/{event_id}/invitations", response_model=InvitationOut, status_code=201)
def create_invitation(event_id: int, body: InvitationIn, db: Session = Depends(get_db)):
    get_event(db, event_id)
    inv = service.create_invitation(db, event_id, body)
    db.commit()
    return inv


@router.get("/invitations/{invitation_id}", response_model=InvitationOut)
def get_invitation(invitation_id: int, db: Session = Depends(get_db)):
    return _inv(db, invitation_id)


@router.put("/invitations/{invitation_id}", response_model=InvitationOut)
def update_invitation(invitation_id: int, body: InvitationIn, db: Session = Depends(get_db)):
    inv = _inv(db, invitation_id)
    service.apply_input(db, inv, body)
    db.commit()
    return inv


@router.delete("/invitations/{invitation_id}", status_code=204)
def delete_invitation(invitation_id: int, db: Session = Depends(get_db)):
    db.delete(_inv(db, invitation_id))
    db.commit()


@router.get("/events/{event_id}/groups", response_model=list[GroupOut])
def list_groups(event_id: int, db: Session = Depends(get_db)):
    get_event(db, event_id)
    return db.scalars(select(Group).where(Group.event_id == event_id).order_by(Group.name)).all()


@router.put("/groups/{group_id}", response_model=GroupOut)
def rename_group(group_id: int, body: GroupIn, db: Session = Depends(get_db)):
    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(404, "group_not_found")
    group.name = body.name.strip()
    db.commit()
    return group


@router.delete("/groups/{group_id}", status_code=204)
def delete_group(group_id: int, db: Session = Depends(get_db)):
    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(404, "group_not_found")
    db.delete(group)  # invitations keep existing; their group becomes empty (FK SET NULL)
    db.commit()
