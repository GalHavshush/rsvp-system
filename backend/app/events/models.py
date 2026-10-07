from datetime import date, datetime, time

from sqlalchemy import DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Event(Base):
    __tablename__ = "event"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    type: Mapped[str] = mapped_column(default="wedding")
    date: Mapped[date | None]
    time: Mapped[time | None]
    venue: Mapped[str | None]
    address: Mapped[str | None]
    waze_url: Mapped[str | None]
    maps_url: Mapped[str | None]
    hosts: Mapped[str | None]
    rsvp_deadline: Mapped[date | None]
    default_language: Mapped[str] = mapped_column(default="he")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
