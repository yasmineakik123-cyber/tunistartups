"""add email to users

Revision ID: 1b7c4f0a2e89
Revises: 0753bee6f9f4
Create Date: 2026-01-16 22:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1b7c4f0a2e89"
down_revision = "0753bee6f9f4"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("email", sa.String(length=255), nullable=False))
    op.create_index("ix_users_email", "users", ["email"], unique=True)


def downgrade():
    op.drop_index("ix_users_email", table_name="users")
    op.drop_column("users", "email")
