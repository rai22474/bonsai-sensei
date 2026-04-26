"""create_bonsai_photo_table

Revision ID: b1c2d3e4f5a6
Revises: a1b2c3d4e5f6
Create Date: 2026-04-25 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()
    if 'bonsai_photo' not in existing_tables:
        op.create_table(
            'bonsai_photo',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('bonsai_id', sa.Integer(), nullable=False),
            sa.Column('file_path', sa.String(), nullable=False),
            sa.Column('taken_on', sa.Date(), nullable=False),
            sa.ForeignKeyConstraint(['bonsai_id'], ['bonsai.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_bonsai_photo_bonsai_id'), 'bonsai_photo', ['bonsai_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_bonsai_photo_bonsai_id'), table_name='bonsai_photo')
    op.drop_table('bonsai_photo')
