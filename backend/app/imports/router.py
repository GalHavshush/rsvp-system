from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth.deps import current_admin
from app.core.db import get_db
from app.events.router import get_event
from app.imports import mapping as mp
from app.imports import pipeline
from app.imports.pipeline import ImportBlocked
from app.imports.parser import MAX_BYTES, ParseError, parse_upload
from app.imports.schemas import CommitRequest, CommitResult, ParsedSheet, Preview, PreviewRequest

router = APIRouter(prefix="/api/events/{event_id}/imports", dependencies=[Depends(current_admin)])


def _check(db: Session, event_id: int, body: PreviewRequest) -> None:
    get_event(db, event_id)
    if err := mp.validate_mapping(body.mapping):
        raise HTTPException(400, err)


@router.post("/parse", response_model=ParsedSheet)
async def parse(event_id: int, file: UploadFile, db: Session = Depends(get_db)):
    get_event(db, event_id)
    data = await file.read(MAX_BYTES + 1)
    try:
        headers, rows = parse_upload(file.filename or "", data)
    except ParseError as e:
        raise HTTPException(400, e.code)
    return ParsedSheet(headers=headers, rows=rows, mapping=mp.detect_mapping(headers))


# The client holds the parsed sheet between steps, so the server keeps no import state;
# commit re-runs validation itself and never trusts the preview.
@router.post("/preview", response_model=Preview)
def preview(event_id: int, body: PreviewRequest, db: Session = Depends(get_db)):
    _check(db, event_id, body)
    return pipeline.build_preview(db, event_id, body.rows, body.mapping)


@router.post("/commit", response_model=CommitResult)
def commit(event_id: int, body: CommitRequest, db: Session = Depends(get_db)):
    _check(db, event_id, body)
    try:
        return pipeline.commit(db, event_id, body.rows, body.mapping, body.actions)
    except ImportBlocked as e:
        raise HTTPException(409, e.code)
