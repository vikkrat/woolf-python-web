"""Create contacts."""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("first_name", sa.String(80), nullable=False),
        sa.Column("last_name", sa.String(80), nullable=False),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("phone", sa.String(32), nullable=False),
        sa.Column("birthday", sa.Date(), nullable=False),
        sa.Column("additional_data", sa.Text(), nullable=True),
    )


def downgrade():
    op.drop_table("contacts")
