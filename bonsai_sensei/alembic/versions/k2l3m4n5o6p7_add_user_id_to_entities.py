"""add_user_id_to_entities

Revision ID: k2l3m4n5o6p7
Revises: j1k2l3m4n5o6
Create Date: 2026-06-06 00:00:00.000000
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = 'k2l3m4n5o6p7'
down_revision: Union[str, Sequence[str], None] = 'j1k2l3m4n5o6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    bonsai_cols = [col['name'] for col in inspector.get_columns('bonsai')]
    if 'user_id' not in bonsai_cols:
        op.add_column('bonsai', sa.Column('user_id', sa.String(), nullable=True))
        op.create_index('ix_bonsai_user_id', 'bonsai', ['user_id'])
        op.create_foreign_key('fk_bonsai_user_id', 'bonsai', 'user_settings', ['user_id'], ['user_id'])

    fertilizer_cols = [col['name'] for col in inspector.get_columns('fertilizer')]
    if 'user_id' not in fertilizer_cols:
        op.add_column('fertilizer', sa.Column('user_id', sa.String(), nullable=True))
        op.create_index('ix_fertilizer_user_id', 'fertilizer', ['user_id'])
        op.create_foreign_key('fk_fertilizer_user_id', 'fertilizer', 'user_settings', ['user_id'], ['user_id'])
        try:
            op.drop_index('ix_fertilizer_name', 'fertilizer')
        except Exception:
            pass

    phytosanitary_cols = [col['name'] for col in inspector.get_columns('phytosanitary')]
    if 'user_id' not in phytosanitary_cols:
        op.add_column('phytosanitary', sa.Column('user_id', sa.String(), nullable=True))
        op.create_index('ix_phytosanitary_user_id', 'phytosanitary', ['user_id'])
        op.create_foreign_key('fk_phytosanitary_user_id', 'phytosanitary', 'user_settings', ['user_id'], ['user_id'])
        try:
            op.drop_index('ix_phytosanitary_name', 'phytosanitary')
        except Exception:
            pass


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    bonsai_cols = [col['name'] for col in inspector.get_columns('bonsai')]
    if 'user_id' in bonsai_cols:
        op.drop_constraint('fk_bonsai_user_id', 'bonsai', type_='foreignkey')
        op.drop_index('ix_bonsai_user_id', 'bonsai')
        op.drop_column('bonsai', 'user_id')

    fertilizer_cols = [col['name'] for col in inspector.get_columns('fertilizer')]
    if 'user_id' in fertilizer_cols:
        op.drop_constraint('fk_fertilizer_user_id', 'fertilizer', type_='foreignkey')
        op.drop_index('ix_fertilizer_user_id', 'fertilizer')
        op.drop_column('fertilizer', 'user_id')

    phytosanitary_cols = [col['name'] for col in inspector.get_columns('phytosanitary')]
    if 'user_id' in phytosanitary_cols:
        op.drop_constraint('fk_phytosanitary_user_id', 'phytosanitary', type_='foreignkey')
        op.drop_index('ix_phytosanitary_user_id', 'phytosanitary')
        op.drop_column('phytosanitary', 'user_id')
