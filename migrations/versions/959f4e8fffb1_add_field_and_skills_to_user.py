"""add field and skills to user

Revision ID: 959f4e8fffb1
Revises: 512c1c8607d1
Create Date: (leave as is)
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "959f4e8fffb1"
down_revision = "512c1c8607d1"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("field", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("skills", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("skills")
        batch_op.drop_column("field")