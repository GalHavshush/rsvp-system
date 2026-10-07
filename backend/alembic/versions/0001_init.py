"""users, sessions, events"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("password_hash", sa.String, nullable=False),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("disabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("role in ('owner','admin')", name="ck_user_role"),
    )
    op.create_table(
        "session",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "event",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("type", sa.String(50), nullable=False, server_default="wedding"),
        sa.Column("date", sa.Date),
        sa.Column("time", sa.Time),
        sa.Column("venue", sa.String(200)),
        sa.Column("address", sa.String(300)),
        sa.Column("waze_url", sa.String(500)),
        sa.Column("maps_url", sa.String(500)),
        sa.Column("hosts", sa.String(300)),
        sa.Column("rsvp_deadline", sa.Date),
        sa.Column("default_language", sa.String(5), nullable=False, server_default="he"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    for t in ("event", "session", "user"):
        op.drop_table(t)
