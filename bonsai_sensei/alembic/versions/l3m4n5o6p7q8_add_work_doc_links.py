"""add_work_doc_links

Revision ID: l3m4n5o6p7q8
Revises: k2l3m4n5o6p7
Create Date: 2026-06-10 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'l3m4n5o6p7q8'
down_revision: Union[str, Sequence[str], None] = 'k2l3m4n5o6p7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    plannedwork_columns = [col['name'] for col in inspector.get_columns('plannedwork')]
    if 'refinement_wiki_path' not in plannedwork_columns:
        op.add_column('plannedwork', sa.Column('refinement_wiki_path', sa.String(), nullable=True))
    if 'result_wiki_path' not in plannedwork_columns:
        op.add_column('plannedwork', sa.Column('result_wiki_path', sa.String(), nullable=True))

    bonsai_photo_columns = [col['name'] for col in inspector.get_columns('bonsai_photo')]
    if 'planned_work_id' in bonsai_photo_columns:
        for fk in inspector.get_foreign_keys('bonsai_photo'):
            if fk.get('referred_table') == 'plannedwork':
                op.drop_constraint(fk['name'], 'bonsai_photo', type_='foreignkey')
        op.drop_column('bonsai_photo', 'planned_work_id')

    existing_tables = inspector.get_table_names()
    if 'planned_work_photo' not in existing_tables:
        op.create_table(
            'planned_work_photo',
            sa.Column('planned_work_id', sa.Integer(), sa.ForeignKey('plannedwork.id', ondelete='CASCADE'), primary_key=True, nullable=False),
            sa.Column('photo_id', sa.Integer(), sa.ForeignKey('bonsai_photo.id', ondelete='CASCADE'), primary_key=True, nullable=False),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_tables = inspector.get_table_names()
    if 'planned_work_photo' in existing_tables:
        op.drop_table('planned_work_photo')

    bonsai_photo_columns = [col['name'] for col in inspector.get_columns('bonsai_photo')]
    if 'planned_work_id' not in bonsai_photo_columns:
        op.add_column('bonsai_photo', sa.Column('planned_work_id', sa.Integer(), nullable=True))
        op.create_foreign_key(
            'fk_bonsai_photo_planned_work_id',
            'bonsai_photo', 'plannedwork',
            ['planned_work_id'], ['id'],
            ondelete='SET NULL',
        )

    plannedwork_columns = [col['name'] for col in inspector.get_columns('plannedwork')]
    if 'result_wiki_path' in plannedwork_columns:
        op.drop_column('plannedwork', 'result_wiki_path')
    if 'refinement_wiki_path' in plannedwork_columns:
        op.drop_column('plannedwork', 'refinement_wiki_path')
