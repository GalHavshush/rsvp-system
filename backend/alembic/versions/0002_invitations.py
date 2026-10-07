"""groups, invitations, members, contacts"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"


def upgrade() -> None:
    op.create_table(
        "guest_group",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("event_id", sa.Integer, sa.ForeignKey("event.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.UniqueConstraint("event_id", "name"),
    )
    op.create_table(
        "invitation",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("event_id", sa.Integer, sa.ForeignKey("event.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("display_name", sa.String, nullable=False),
        sa.Column("group_id", sa.Integer, sa.ForeignKey("guest_group.id", ondelete="SET NULL")),
        sa.Column("rsvp_token", sa.String, nullable=False, unique=True),
        sa.Column("rsvp_status", sa.String, nullable=False, server_default="no_response"),
        sa.Column("attendee_count", sa.Integer),
        sa.Column("rsvp_updated_at", sa.DateTime(timezone=True)),
        sa.Column("rsvp_source", sa.String),
        sa.Column("rsvp_note", sa.Text),
        sa.Column("notes", sa.Text),
        sa.Column("include_maybe_in_seating", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("message_state", sa.String, nullable=False, server_default="not_prepared"),
        sa.CheckConstraint("rsvp_status in ('no_response','coming','not_coming','maybe')", name="ck_inv_status"),
        sa.CheckConstraint("attendee_count is null or attendee_count >= 0", name="ck_inv_count"),
        sa.CheckConstraint("rsvp_source is null or rsvp_source in ('guest_web','admin_manual','whatsapp')", name="ck_inv_source"),
    )
    op.create_table(
        "invitation_member",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("invitation_id", sa.Integer, sa.ForeignKey("invitation.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_table(
        "invitation_contact",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("invitation_id", sa.Integer, sa.ForeignKey("invitation.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("member_id", sa.Integer, sa.ForeignKey("invitation_member.id", ondelete="SET NULL")),
        sa.Column("phone_raw", sa.String, nullable=False),
        sa.Column("phone_e164", sa.String, index=True),
        sa.Column("phone_valid", sa.Boolean, nullable=False),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
    )


def downgrade() -> None:
    for t in ("invitation_contact", "invitation_member", "invitation", "guest_group"):
        op.drop_table(t)
