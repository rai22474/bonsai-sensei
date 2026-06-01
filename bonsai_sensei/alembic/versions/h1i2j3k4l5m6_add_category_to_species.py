"""add_category_to_species

Revision ID: h1i2j3k4l5m6
Revises: g1h2i3j4k5l6
Create Date: 2026-05-09 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'h1i2j3k4l5m6'
down_revision: Union[str, Sequence[str], None] = 'g1h2i3j4k5l6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    species_columns = [col['name'] for col in inspector.get_columns('species')]
    if 'category' not in species_columns:
        op.add_column(
            'species',
            sa.Column('category', sa.String(), nullable=False, server_default='unknown'),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    species_columns = [col['name'] for col in inspector.get_columns('species')]
    if 'category' in species_columns:
        op.drop_column('species', 'category')
