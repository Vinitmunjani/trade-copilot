"""Add trade_logs table for append-only trade event audit log

Revision ID: 0004_add_trade_logs_table
Revises: 0003_migrate_user_accounts
Create Date: 2026-02-28
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0004_add_trade_logs_table'
down_revision = '0003_migrate_user_accounts'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create trade_logs table."""
    op.create_table(
        'trade_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('trade_id', sa.String(36), sa.ForeignKey('trades.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('payload', sa.JSON, nullable=True),
        sa.Column('note', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_trade_logs_trade_id', 'trade_logs', ['trade_id'])
    op.create_index('ix_trade_logs_user_id', 'trade_logs', ['user_id'])
    op.create_index('ix_trade_logs_event_type', 'trade_logs', ['event_type'])
    op.create_index('ix_trade_logs_created_at', 'trade_logs', ['created_at'])


def downgrade() -> None:
    """Drop trade_logs table."""
    op.drop_index('ix_trade_logs_created_at', table_name='trade_logs')
    op.drop_index('ix_trade_logs_event_type', table_name='trade_logs')
    op.drop_index('ix_trade_logs_user_id', table_name='trade_logs')
    op.drop_index('ix_trade_logs_trade_id', table_name='trade_logs')
    op.drop_table('trade_logs')
