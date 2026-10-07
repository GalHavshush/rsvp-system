import secrets
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Group(Base):
    __tablename__ = "guest_group"
    __table_args__ = (UniqueConstraint("event_id", "name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id", ondelete="CASCADE"))
    name: Mapped[str]


class Invitation(Base):
    __tablename__ = "invitation"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id", ondelete="CASCADE"), index=True)
    display_name: Mapped[str]
    group_id: Mapped[int | None] = mapped_column(ForeignKey("guest_group.id", ondelete="SET NULL"))
    rsvp_token: Mapped[str] = mapped_column(unique=True, default=lambda: secrets.token_urlsafe(24))
    rsvp_status: Mapped[str] = mapped_column(default="no_response")
    attendee_count: Mapped[int | None]
    rsvp_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rsvp_source: Mapped[str | None]
    rsvp_note: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    include_maybe_in_seating: Mapped[bool] = mapped_column(default=False)
    message_state: Mapped[str] = mapped_column(default="not_prepared")

    group: Mapped[Group | None] = relationship()
    members: Mapped[list["InvitationMember"]] = relationship(
        cascade="all, delete-orphan", order_by="InvitationMember.position")
    contacts: Mapped[list["InvitationContact"]] = relationship(
        cascade="all, delete-orphan", order_by="InvitationContact.position")

    @property
    def group_name(self) -> str | None:
        return self.group.name if self.group else None


class InvitationMember(Base):
    __tablename__ = "invitation_member"
    id: Mapped[int] = mapped_column(primary_key=True)
    invitation_id: Mapped[int] = mapped_column(ForeignKey("invitation.id", ondelete="CASCADE"), index=True)
    name: Mapped[str]
    position: Mapped[int] = mapped_column(default=0)


class InvitationContact(Base):
    __tablename__ = "invitation_contact"
    id: Mapped[int] = mapped_column(primary_key=True)
    invitation_id: Mapped[int] = mapped_column(ForeignKey("invitation.id", ondelete="CASCADE"), index=True)
    member_id: Mapped[int | None] = mapped_column(ForeignKey("invitation_member.id", ondelete="SET NULL"))
    phone_raw: Mapped[str]
    phone_e164: Mapped[str | None] = mapped_column(index=True)
    phone_valid: Mapped[bool]
    position: Mapped[int] = mapped_column(default=0)
