"""replace_care_guide_with_wiki_path

Revision ID: 644fe3ae93f1
Revises:
Create Date: 2026-04-21 15:39:35.712004

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '644fe3ae93f1'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    existing_tables = sa.inspect(bind).get_table_names()

    if 'species' not in existing_tables:
        from sqlmodel import SQLModel
        from bonsai_sensei.domain import species, bonsai, fertilizer, phytosanitary, bonsai_event, user_settings, planned_work
        SQLModel.metadata.create_all(bind)
    else:
        op.add_column('species', sa.Column('wiki_path', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
        op.drop_column('species', 'care_guide')


def downgrade() -> None:
    op.add_column('species', sa.Column('care_guide', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.drop_column('species', 'wiki_path')
