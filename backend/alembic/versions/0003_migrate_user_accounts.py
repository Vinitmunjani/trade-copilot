"""Migrate existing user metaapi_account_id to meta_accounts table

Revision ID: 0003_migrate_user_accounts
Revises: 0002_add_meta_accounts
Create Date: 2026-02-25
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone
import uuid

# revision identifiers, used by Alembic.
revision = '0003_migrate_user_accounts'
down_revision = '0002_add_meta_accounts'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Migrate existing user.metaapi_account_id entries to meta_accounts table."""
    connection = op.get_bind()
    
    # Get all users with metaapi_account_id set
    users = connection.execute(sa.text(
        "SELECT id, metaapi_account_id, mt_login, mt_server, mt_platform, mt_last_heartbeat "
        "FROM users WHERE metaapi_account_id IS NOT NULL"
    )).fetchall()
    
    now = datetime.now(timezone.utc)
    
    for user_row in users:
        user_id, metaapi_account_id, mt_login, mt_server, mt_platform, mt_last_heartbeat = user_row
        
        # Check if already migrated
        existing = connection.execute(sa.text(
            "SELECT 1 FROM meta_accounts WHERE metaapi_account_id = :account_id"
        ), {"account_id": metaapi_account_id}).fetchone()
        
        if not existing:
            # Insert into meta_accounts
            meta_account_id = uuid.uuid4()
            connection.execute(sa.text(
                """INSERT INTO meta_accounts 
                (id, user_id, metaapi_account_id, mt_login, mt_server, mt_platform, mt_last_heartbeat, created_at, updated_at)
                VALUES (:id, :user_id, :account_id, :login, :server, :platform, :heartbeat, :created, :updated)"""
            ), {
                "id": meta_account_id,
                "user_id": user_id,
                "account_id": metaapi_account_id,
                "login": mt_login,
                "server": mt_server,
                "platform": mt_platform or "mt5",
                "heartbeat": mt_last_heartbeat,
                "created": now,
                "updated": now,
            })
    
    connection.commit()


def downgrade() -> None:
    """Downgrade will drop the meta_accounts table (handled in previous migration)."""
    pass

