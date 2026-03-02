"""add trial account claims table

Revision ID: 0005_add_trial_account_claims
Revises: 0004_add_trade_logs_table
Create Date: 2026-03-02
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0005_add_trial_account_claims"
down_revision = "0004_add_trade_logs_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("trial_account_claims"):
        return

    op.create_table(
        "trial_account_claims",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("fingerprint", sa.String(length=255), nullable=False),
        sa.Column("mt_login", sa.String(length=50), nullable=False),
        sa.Column("mt_server", sa.String(length=255), nullable=False),
        sa.Column("mt_platform", sa.String(length=10), nullable=False, server_default="mt5"),
        sa.Column("first_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("last_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("claim_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("first_claimed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_claimed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("fingerprint", name="uq_trial_account_claims_fingerprint"),
    )
    op.create_index("ix_trial_account_claims_fingerprint", "trial_account_claims", ["fingerprint"])
    op.create_index("ix_trial_account_claims_first_user_id", "trial_account_claims", ["first_user_id"])
    op.create_index("ix_trial_account_claims_last_user_id", "trial_account_claims", ["last_user_id"])


def downgrade() -> None:
    op.drop_index("ix_trial_account_claims_last_user_id", table_name="trial_account_claims")
    op.drop_index("ix_trial_account_claims_first_user_id", table_name="trial_account_claims")
    op.drop_index("ix_trial_account_claims_fingerprint", table_name="trial_account_claims")
    op.drop_table("trial_account_claims")
