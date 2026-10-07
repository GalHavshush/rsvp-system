import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.auth.models import SessionRow, User
from app.core.config import settings

_ph = PasswordHasher()
# Verified against when the email is unknown, so timing doesn't reveal which emails exist.
_DUMMY_HASH = _ph.hash("dummy-password")


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def needs_setup(db: Session) -> bool:
    return db.scalar(select(User.id).limit(1)) is None


def create_user(db: Session, email: str, password: str, role: str) -> User:
    user = User(email=email.lower(), password_hash=_ph.hash(password), role=role)
    db.add(user)
    db.commit()
    return user


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == email.lower()))
    try:
        _ph.verify(user.password_hash if user else _DUMMY_HASH, password)
    except VerifyMismatchError:
        return None
    return user if user and not user.disabled else None


def start_session(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    db.add(SessionRow(
        token_hash=_hash(token), user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(days=settings.session_days),
    ))
    db.commit()
    return token


def user_for_token(db: Session, token: str) -> User | None:
    row = db.get(SessionRow, _hash(token))
    if not row or row.expires_at < datetime.now(UTC):
        return None
    user = db.get(User, row.user_id)
    return user if user and not user.disabled else None


def end_session(db: Session, token: str) -> None:
    db.execute(delete(SessionRow).where(SessionRow.token_hash == _hash(token)))
    db.commit()
