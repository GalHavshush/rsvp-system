from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import current_admin
from app.core.db import get_db
from app.events.models import Event
from app.events.schemas import EventIn, EventOut

router = APIRouter(prefix="/api/events", dependencies=[Depends(current_admin)])


def _get(db: Session, event_id: int) -> Event:
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(404, "event_not_found")
    return event


@router.get("", response_model=list[EventOut])
def list_events(db: Session = Depends(get_db)):
    return db.query(Event).order_by(Event.id).all()


@router.post("", response_model=EventOut, status_code=201)
def create_event(body: EventIn, db: Session = Depends(get_db)):
    event = Event(**body.model_dump())
    db.add(event)
    db.commit()
    return event


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)):
    return _get(db, event_id)


@router.put("/{event_id}", response_model=EventOut)
def update_event(event_id: int, body: EventIn, db: Session = Depends(get_db)):
    event = _get(db, event_id)
    for k, v in body.model_dump().items():
        setattr(event, k, v)
    db.commit()
    return event


@router.delete("/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    db.delete(_get(db, event_id))
    db.commit()
