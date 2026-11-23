"""Create the university schema."""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "groups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
    )
    op.create_table(
        "teachers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
    )
    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False),
    )
    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False, unique=True),
        sa.Column(
            "teacher_id", sa.Integer(), sa.ForeignKey("teachers.id"), nullable=False
        ),
    )
    op.create_table(
        "grades",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "student_id", sa.Integer(), sa.ForeignKey("students.id"), nullable=False
        ),
        sa.Column(
            "subject_id", sa.Integer(), sa.ForeignKey("subjects.id"), nullable=False
        ),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("received_at", sa.Date(), nullable=False),
        sa.CheckConstraint("value BETWEEN 1 AND 100", name="grade_range"),
    )
    for table, column in [
        ("students", "group_id"),
        ("subjects", "teacher_id"),
        ("grades", "student_id"),
        ("grades", "subject_id"),
    ]:
        op.create_index(f"ix_{table}_{column}", table, [column])


def downgrade():
    for table in ("grades", "subjects", "students", "teachers", "groups"):
        op.drop_table(table)
