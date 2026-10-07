import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres@localhost:5433/rsvp_test")

import pytest
from fastapi.testclient import TestClient

from app.core.db import Base, engine
from app.auth.router import _attempts
from app.main import app


@pytest.fixture()
def client():
    _attempts.clear()  # login throttle is process-global
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return TestClient(app, headers={"X-Requested-With": "rsvp"})
