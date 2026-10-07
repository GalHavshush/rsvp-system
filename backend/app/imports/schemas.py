from typing import Literal

from pydantic import BaseModel

from app.invitations.schemas import InvitationIn

Action = Literal["skip", "update", "new"]


class ParsedSheet(BaseModel):
    headers: list[str]
    rows: list[list[str]]
    mapping: list[str]


class PreviewRequest(BaseModel):
    mapping: list[str]
    rows: list[list[str]]


class CommitRequest(PreviewRequest):
    actions: dict[int, Action] = {}  # row index -> chosen action; missing = default_action


class Issue(BaseModel):
    code: str  # missing_name | invalid_phone | duplicate_phone_in_file | duplicate_row | existing_phone | existing_name
    level: Literal["error", "warning", "conflict"]
    detail: str | None = None


class Conflict(BaseModel):
    invitation_id: int
    invitation_name: str


class PreviewRow(BaseModel):
    index: int
    draft: InvitationIn | None
    status: Literal["ok", "warning", "conflict", "error"]
    issues: list[Issue]
    conflict: Conflict | None = None
    default_action: Action


class Preview(BaseModel):
    rows: list[PreviewRow]
    counts: dict[str, int]


class CommitResult(BaseModel):
    created: int
    updated: int
    skipped: int
