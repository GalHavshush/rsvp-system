from alembic import context
from sqlalchemy import create_engine

from app.core.config import settings
from app.core.db import Base
import app.auth.models, app.events.models, app.invitations.models  # noqa: F401  (register tables)

with create_engine(settings.database_url).connect() as conn:
    context.configure(connection=conn, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
