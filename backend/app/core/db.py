from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    with Session(engine) as db:
        yield db
