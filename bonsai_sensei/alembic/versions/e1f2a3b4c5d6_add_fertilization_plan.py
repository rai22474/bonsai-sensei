"""add_fertilization_plan

Revision ID: e1f2a3b4c5d6
Revises: d1e2f3a4b5c6
Create Date: 2026-05-06 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, Sequence[str], None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if 'fertilizationplan' not in existing_tables:
        op.create_table(
            'fertilizationplan',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('bonsai_id', sa.Integer(), nullable=False),
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
    if 'plan_id' not in plannedwork_columns:
        op.add_column(
            'plannedwork',
            sa.Column('plan_id', sa.Integer(), nullable=True),
        )
        op.create_foreign_key(
            'fk_plannedwork_plan_id',
            'plannedwork', 'fertilizationplan',
            ['plan_id'], ['id'],
            ondelete='SET NULL',
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    plannedwork_columns = [col['name'] for col in inspector.get_columns('plannedwork')]
    if 'plan_id' in plannedwork_columns:
        op.drop_constraint('fk_plannedwork_plan_id', 'plannedwork', type_='foreignkey')
        op.drop_column('plannedwork', 'plan_id')

    existing_tables = inspector.get_table_names()
    if 'fertilizationplan' in existing_tables:
        op.drop_table('fertilizationplan')
