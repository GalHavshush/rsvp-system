import time
from collections import defaultdict

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import service
from app.auth.deps import COOKIE, current_admin, require_owner
from app.auth.models import User
from app.auth.schemas import Credentials, SetupStatus, UserOut
from app.core.config import settings
from app.core.db import get_db

router = APIRouter(prefix="/api")

# ponytail: in-memory per-IP throttle, single worker only; move to Redis/DB if scaled out.
_attempts: dict[str, list[float]] = defaultdict(list)


def _throttle(request: Request, limit: int = 10, window: int = 300) -> None:
    ip = request.client.host if request.client else "?"
    now = time.monotonic()
    _attempts[ip] = [t for t in _attempts[ip] if now - t < window]
    if len(_attempts[ip]) >= limit:
        raise HTTPException(429, "too_many_attempts")
    _attempts[ip].append(now)


def _login(db: Session, user: User, response: Response) -> None:
    response.set_cookie(
        COOKIE, service.start_session(db, user), max_age=settings.session_days * 86400,
        httponly=True, secure=settings.cookie_secure, samesite="lax", path="/",
    )


@router.get("/auth/status", response_model=SetupStatus)
def status(db: Session = Depends(get_db)):
    return SetupStatus(needs_setup=service.needs_setup(db))


@router.post("/auth/setup", response_model=UserOut)
def setup(body: Credentials, response: Response, request: Request, db: Session = Depends(get_db)):
    _throttle(request)
    if not service.needs_setup(db):
        raise HTTPException(409, "already_set_up")
    try:
        user = service.create_user(db, body.email, body.password, "owner")
    except IntegrityError:  # lost a setup race
        db.rollback()
        raise HTTPException(409, "already_set_up")
    _login(db, user, response)
    return user


@router.post("/auth/login", response_model=UserOut)
def login(body: Credentials, response: Response, request: Request, db: Session = Depends(get_db)):
    _throttle(request)
    user = service.authenticate(db, body.email, body.password)
    if not user:
        raise HTTPException(401, "invalid_credentials")
    _login(db, user, response)
    return user


@router.post("/auth/logout", status_code=204)
def logout(response: Response, token: str | None = Cookie(None, alias=COOKIE), db: Session = Depends(get_db)):
    if token:
        service.end_session(db, token)
    response.delete_cookie(COOKIE, path="/")


@router.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(current_admin)):
    return user


@router.get("/users", response_model=list[UserOut])
def list_users(_: User = Depends(require_owner), db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()


@router.post("/users", response_model=UserOut, status_code=201)
def create_admin(body: Credentials, _: User = Depends(require_owner), db: Session = Depends(get_db)):
    try:
        return service.create_user(db, body.email, body.password, "admin")
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "email_taken")
