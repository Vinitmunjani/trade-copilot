"""add meta_accounts table for multi-account MetaAPI support

Revision ID: 0002_add_meta_accounts
Revises: 0001_add_subscription
Create Date: 2026-02-25
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_add_meta_accounts'
down_revision = '0001_add_subscription'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'meta_accounts',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('user_id', sa.Uuid(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('metaapi_account_id', sa.String(length=255), nullable=True),
        sa.Column('mt_login', sa.String(length=50), nullable=True),
        sa.Column('mt_server', sa.String(length=255), nullable=True),
        sa.Column('mt_platform', sa.String(length=10), nullable=True, server_default='mt5'),
        sa.Column('mt_last_heartbeat', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('meta_accounts')

