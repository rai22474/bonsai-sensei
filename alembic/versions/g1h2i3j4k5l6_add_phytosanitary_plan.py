"""add_phytosanitary_plan

Revision ID: g1h2i3j4k5l6
Revises: f1a2b3c4d5e6
Create Date: 2026-05-08 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'g1h2i3j4k5l6'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if 'phytosanitaryplan' not in existing_tables:
        op.create_table(
            'phytosanitaryplan',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('bonsai_id', sa.Integer(), nullable=False),
            sa.Column('period_start', sa.Date(), nullable=False),
            sa.Column('period_end', sa.Date(), nullable=False),
            sa.Column('status', sa.String(), nullable=False, server_default='active'),
            sa.Column('goal', sa.String(), nullable=True),
            sa.Column('wiki_path', sa.String(), nullable=False),
            sa.Column('abandonment_reason', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('abandoned_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['bonsai_id'], ['bonsai.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )

    plannedwork_columns = [col['name'] for col in inspector.get_columns('plannedwork')]
    if 'phytosanitary_plan_id' not in plannedwork_columns:
        op.add_column(
            'plannedwork',
            sa.Column('phytosanitary_plan_id', sa.Integer(), nullable=True),
        )
        op.create_foreign_key(
            'fk_plannedwork_phytosanitary_plan_id',
            'plannedwork', 'phytosanitaryplan',
            ['phytosanitary_plan_id'], ['id'],
            ondelete='SET NULL',
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    plannedwork_columns = [col['name'] for col in inspector.get_columns('plannedwork')]
    if 'phytosanitary_plan_id' in plannedwork_columns:
        op.drop_constraint('fk_plannedwork_phytosanitary_plan_id', 'plannedwork', type_='foreignkey')
        op.drop_column('plannedwork', 'phytosanitary_plan_id')

    existing_tables = inspector.get_table_names()
    if 'phytosanitaryplan' in existing_tables:
        op.drop_table('phytosanitaryplan')
