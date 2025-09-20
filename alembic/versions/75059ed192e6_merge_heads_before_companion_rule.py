"""merge heads before companion rule

Revision ID: 75059ed192e6
Revises: 54443d2e77a9, a1b2c3d4e5f6
Create Date: 2025-09-20 14:41:51.693846

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75059ed192e6'
down_revision: Union[str, Sequence[str], None] = ('54443d2e77a9', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
