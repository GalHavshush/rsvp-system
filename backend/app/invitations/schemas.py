from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

RsvpStatus = Literal["no_response", "coming", "not_coming", "maybe"]


class MemberIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class ContactIn(BaseModel):
    phone: str = Field(min_length=1, max_length=50)
    member_index: int | None = None  # index into InvitationIn.members


class InvitationIn(BaseModel):
    display_name: str = Field(min_length=1, max_length=200)
    group_name: str | None = Field(None, max_length=100)
    notes: str | None = None
    members: list[MemberIn] = []
    contacts: list[ContactIn] = []

    @model_validator(mode="after")
    def _member_refs(self):
        for c in self.contacts:
            if c.member_index is not None and not 0 <= c.member_index < len(self.members):
                raise ValueError("member_index out of range")
        return self


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class ContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    member_id: int | None
    phone_raw: str
    phone_e164: str | None
    phone_valid: bool


class InvitationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    event_id: int
    display_name: str
    group_name: str | None
    rsvp_token: str
    rsvp_status: RsvpStatus
    attendee_count: int | None
    rsvp_updated_at: datetime | None
    rsvp_source: str | None
    notes: str | None
    message_state: str
    members: list[MemberOut]
    contacts: list[ContactOut]


class InvitationPage(BaseModel):
    items: list[InvitationOut]
    total: int


class GroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class GroupIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
