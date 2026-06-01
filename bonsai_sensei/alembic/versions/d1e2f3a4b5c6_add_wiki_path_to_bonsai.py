"""add_wiki_path_to_bonsai

Revision ID: d1e2f3a4b5c6
Revises: b1c2d3e4f5a6
Create Date: 2026-05-05 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, Sequence[str], None] = 'c2d3e4f5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [col['name'] for col in inspector.get_columns('bonsai')]
    if 'wiki_path' not in columns:
        op.add_column('bonsai', sa.Column('wiki_path', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('bonsai', 'wiki_path')
