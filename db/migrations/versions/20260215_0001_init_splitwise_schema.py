"""init splitwise schema

Revision ID: 202602150001
Revises:
Create Date: 2026-02-15 00:01:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "202602150001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email_lower", "users", [sa.text("lower(email)")], unique=True)

    op.create_table(
        "groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_groups_created_by_user_id", "groups", ["created_by_user_id"], unique=False)

    op.create_table(
        "group_members",
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=20), server_default="member", nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("role IN ('owner','member')", name="ck_group_members_role"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("group_id", "user_id"),
    )
    op.create_index("ix_group_members_user_id", "group_members", ["user_id"], unique=False)

    op.create_table(
        "expenses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("paid_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("split_method", sa.String(length=20), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("char_length(currency_code) = 3", name="ck_expenses_currency_code_len"),
        sa.CheckConstraint("split_method IN ('equal','percentage','exact')", name="ck_expenses_split_method"),
        sa.CheckConstraint("total_amount > 0", name="ck_expenses_total_amount_positive"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["paid_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_expenses_group_id_created_at", "expenses", ["group_id", "created_at"], unique=False)
    op.create_index("ix_expenses_paid_by_user_id", "expenses", ["paid_by_user_id"], unique=False)

    op.create_table(
        "expense_participants",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expense_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("share_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("share_percentage", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "share_amount >= 0", name="ck_expense_participants_share_amount_non_negative"
        ),
        sa.CheckConstraint(
            "share_percentage IS NULL OR (share_percentage >= 0 AND share_percentage <= 100)",
            name="ck_expense_participants_share_percentage_range",
        ),
        sa.ForeignKeyConstraint(["expense_id"], ["expenses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("expense_id", "user_id", name="uq_expense_participants_expense_user"),
    )
    op.create_index("ix_expense_participants_user_id", "expense_participants", ["user_id"], unique=False)

    op.create_table(
        "settlements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payer_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payee_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("settled_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_settlements_amount_positive"),
        sa.CheckConstraint("char_length(currency_code) = 3", name="ck_settlements_currency_code_len"),
        sa.CheckConstraint("payer_user_id <> payee_user_id", name="ck_settlements_distinct_users"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["payee_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["payer_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_settlements_group_id_settled_at", "settlements", ["group_id", "settled_at"], unique=False)
    op.create_index("ix_settlements_payer_user_id", "settlements", ["payer_user_id"], unique=False)
    op.create_index("ix_settlements_payee_user_id", "settlements", ["payee_user_id"], unique=False)

    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("debtor_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("creditor_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("entry_type", sa.String(length=20), nullable=False),
        sa.Column("expense_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("settlement_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_ledger_entries_amount_positive"),
        sa.CheckConstraint("char_length(currency_code) = 3", name="ck_ledger_entries_currency_code_len"),
        sa.CheckConstraint("debtor_user_id <> creditor_user_id", name="ck_ledger_entries_distinct_users"),
        sa.CheckConstraint("entry_type IN ('expense','settlement')", name="ck_ledger_entries_entry_type"),
        sa.CheckConstraint(
            "(entry_type = 'expense' AND expense_id IS NOT NULL AND settlement_id IS NULL) OR "
            "(entry_type = 'settlement' AND settlement_id IS NOT NULL AND expense_id IS NULL)",
            name="ck_ledger_entries_ref_by_entry_type",
        ),
        sa.ForeignKeyConstraint(["creditor_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["debtor_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["expense_id"], ["expenses.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["settlement_id"], ["settlements.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ledger_entries_group_id_created_at", "ledger_entries", ["group_id", "created_at"], unique=False)
    op.create_index("ix_ledger_entries_debtor_user_id", "ledger_entries", ["debtor_user_id"], unique=False)
    op.create_index("ix_ledger_entries_creditor_user_id", "ledger_entries", ["creditor_user_id"], unique=False)
    op.create_index("ix_ledger_entries_expense_id", "ledger_entries", ["expense_id"], unique=False)
    op.create_index("ix_ledger_entries_settlement_id", "ledger_entries", ["settlement_id"], unique=False)

    op.create_table(
        "idempotency_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("request_method", sa.String(length=10), nullable=False),
        sa.Column("request_path", sa.String(length=255), nullable=False),
        sa.Column("request_hash", sa.String(length=128), nullable=True),
        sa.Column("response_status_code", sa.Integer(), nullable=True),
        sa.Column("response_body", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("resource_type", sa.String(length=50), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "idempotency_key", name="uq_idempotency_keys_user_key"),
    )
    op.create_index("ix_idempotency_keys_expires_at", "idempotency_keys", ["expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_idempotency_keys_expires_at", table_name="idempotency_keys")
    op.drop_table("idempotency_keys")

    op.drop_index("ix_ledger_entries_settlement_id", table_name="ledger_entries")
    op.drop_index("ix_ledger_entries_expense_id", table_name="ledger_entries")
    op.drop_index("ix_ledger_entries_creditor_user_id", table_name="ledger_entries")
    op.drop_index("ix_ledger_entries_debtor_user_id", table_name="ledger_entries")
    op.drop_index("ix_ledger_entries_group_id_created_at", table_name="ledger_entries")
    op.drop_table("ledger_entries")

    op.drop_index("ix_settlements_payee_user_id", table_name="settlements")
    op.drop_index("ix_settlements_payer_user_id", table_name="settlements")
    op.drop_index("ix_settlements_group_id_settled_at", table_name="settlements")
    op.drop_table("settlements")

    op.drop_index("ix_expense_participants_user_id", table_name="expense_participants")
    op.drop_table("expense_participants")

    op.drop_index("ix_expenses_paid_by_user_id", table_name="expenses")
    op.drop_index("ix_expenses_group_id_created_at", table_name="expenses")
    op.drop_table("expenses")

    op.drop_index("ix_group_members_user_id", table_name="group_members")
    op.drop_table("group_members")

    op.drop_index("ix_groups_created_by_user_id", table_name="groups")
    op.drop_table("groups")

    op.drop_index("ix_users_email_lower", table_name="users")
    op.drop_table("users")
