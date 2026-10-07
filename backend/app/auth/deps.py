from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import service
from app.auth.models import User
from app.core.db import get_db

COOKIE = "session"


def current_admin(token: str | None = Cookie(None, alias=COOKIE), db: Session = Depends(get_db)) -> User:
    user = service.user_for_token(db, token) if token else None
    if not user:
        raise HTTPException(401, "not_authenticated")
    return user


def require_owner(user: User = Depends(current_admin)) -> User:
    if user.role != "owner":
        raise HTTPException(403, "owner_only")
    return user
