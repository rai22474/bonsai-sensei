"""add_development_plan

Revision ID: j1k2l3m4n5o6
Revises: i1j2k3l4m5n6
Create Date: 2026-06-06 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'j1k2l3m4n5o6'
down_revision: Union[str, Sequence[str], None] = 'i1j2k3l4m5n6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if 'developmentplan' not in existing_tables:
        op.create_table(
            'developmentplan',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('bonsai_id', sa.Integer(), nullable=False),
            sa.Column('development_path', sa.String(), nullable=False),
            sa.Column('current_phase', sa.String(), nullable=False),
            sa.Column('target_style', sa.String(), nullable=False),
            sa.Column('design_goal', sa.String(), nullable=False),
            sa.Column('period_start', sa.Date(), nullable=False),
            sa.Column('period_end', sa.Date(), nullable=False),
            sa.Column('status', sa.String(), nullable=False, server_default='active'),
            sa.Column('wiki_path', sa.String(), nullable=False),
            sa.Column('abandonment_reason', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('abandoned_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['bonsai_id'], ['bonsai.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )

    plannedwork_columns = [col['name'] for col in inspector.get_columns('plannedwork')]
    if 'development_plan_id' not in plannedwork_columns:
        op.add_column(
            'plannedwork',
            sa.Column('development_plan_id', sa.Integer(), nullable=True),
        )
        op.create_foreign_key(
            'fk_plannedwork_development_plan_id',
            'plannedwork', 'developmentplan',
            ['development_plan_id'], ['id'],
            ondelete='SET NULL',
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    plannedwork_columns = [col['name'] for col in inspector.get_columns('plannedwork')]
    if 'development_plan_id' in plannedwork_columns:
        op.drop_constraint('fk_plannedwork_development_plan_id', 'plannedwork', type_='foreignkey')
        op.drop_column('plannedwork', 'development_plan_id')

    existing_tables = inspector.get_table_names()
    if 'developmentplan' in existing_tables:
        op.drop_table('developmentplan')
