"""add release optimization

Revision ID: 20261008_opt
Revises: 20261008_coord
Create Date: 2026-10-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20261008_opt'
down_revision = '20261008_coord'
branch_labels = None
depends_on = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
