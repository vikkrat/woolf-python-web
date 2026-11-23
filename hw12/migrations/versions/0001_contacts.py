"""Initial users and owned contacts schema."""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(80), nullable=False, unique=True),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("avatar", sa.String(2048), nullable=True),
        sa.Column("token_version", sa.Integer(), nullable=False),
        sa.CheckConstraint("role IN ('user', 'admin')", name="valid_role"),
    )
    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "owner_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("first_name", sa.String(80), nullable=False),
        sa.Column("last_name", sa.String(80), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("phone", sa.String(32), nullable=False),
        sa.Column("birthday", sa.Date(), nullable=False),
        sa.Column("additional_data", sa.Text(), nullable=True),
        sa.UniqueConstraint("owner_id", "email", name="uq_owner_email"),
    )
    op.create_index("ix_contacts_owner_id", "contacts", ["owner_id"])


def downgrade():
    op.drop_table("contacts")
    op.drop_table("users")
