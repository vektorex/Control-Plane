"""merge

Revision ID: d53cd3eb8cc2
Revises: 041, add_decision_intelligence_step_51
Create Date: 2026-10-08 00:40:55.618505

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd53cd3eb8cc2'
down_revision: Union[str, None] = ('041', 'add_decision_intelligence_step_51')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
