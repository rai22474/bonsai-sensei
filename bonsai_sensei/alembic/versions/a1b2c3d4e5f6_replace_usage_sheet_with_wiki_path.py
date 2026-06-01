"""replace_usage_sheet_with_wiki_path

Revision ID: a1b2c3d4e5f6
Revises: 644fe3ae93f1
Create Date: 2026-04-24 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '644fe3ae93f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    phytosanitary_columns = {col['name'] for col in inspector.get_columns('phytosanitary')}
    if 'wiki_path' not in phytosanitary_columns:
        op.add_column('phytosanitary', sa.Column('wiki_path', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    for col in ('usage_sheet', 'recommended_for', 'sources'):
        if col in phytosanitary_columns:
            op.drop_column('phytosanitary', col)

    fertilizer_columns = {col['name'] for col in inspector.get_columns('fertilizer')}
    if 'wiki_path' not in fertilizer_columns:
        op.add_column('fertilizer', sa.Column('wiki_path', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    for col in ('usage_sheet', 'sources'):
        if col in fertilizer_columns:
            op.drop_column('fertilizer', col)


def downgrade() -> None:
    op.drop_column('phytosanitary', 'wiki_path')
    op.add_column('phytosanitary', sa.Column('usage_sheet', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default=''))
    op.add_column('phytosanitary', sa.Column('recommended_for', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default=''))
    op.add_column('phytosanitary', sa.Column('sources', postgresql.JSON(astext_type=sa.Text()), nullable=True))

    op.drop_column('fertilizer', 'wiki_path')
    op.add_column('fertilizer', sa.Column('usage_sheet', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default=''))
    op.add_column('fertilizer', sa.Column('sources', postgresql.JSON(astext_type=sa.Text()), nullable=True))
