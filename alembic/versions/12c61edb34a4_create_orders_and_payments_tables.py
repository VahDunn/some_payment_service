"""create orders and payments tables

Revision ID: 12c61edb34a4
Revises:
Create Date: 2026-03-12 13:24:56.017888
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "12c61edb34a4"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "orders",
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "payment_status",
            sa.Enum(
                "UNPAID",
                "PARTIALLY_PAID",
                "PAID",
                name="order_payment_status",
            ),
            server_default="UNPAID",
            nullable=False,
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("amount > 0", name="ck_orders_amount_gt_0"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "payments",
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "type",
            sa.Enum("CASH", "ACQUIRING", name="payment_type"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "SUCCEEDED",
                "REFUNDED",
                "FAILED",
                name="payment_status",
            ),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("bank_payment_id", sa.String(length=128), nullable=True),
        sa.Column(
            "bank_status",
            sa.Enum(
                "NEW",
                "PENDING",
                "PAID",
                "FAILED",
                "UNKNOWN",
                name="bank_payment_status",
            ),
            nullable=True,
        ),
        sa.Column("bank_paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("bank_error", sa.Text(), nullable=True),
        sa.Column(
            "refunded_amount",
            sa.Numeric(precision=12, scale=2),
            server_default="0",
            nullable=False,
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("amount > 0", name="ck_payments_amount_gt_0"),
        sa.CheckConstraint(
            "refunded_amount <= amount",
            name="ck_payments_refunded_amount_lte_amount",
        ),
        sa.CheckConstraint(
            "refunded_amount >= 0",
            name="ck_payments_refunded_amount_gte_0",
        ),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bank_payment_id"),
    )

    op.create_index(
        op.f("ix_payments_order_id"),
        "payments",
        ["order_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_payments_order_id"), table_name="payments")
    op.drop_table("payments")
    op.drop_table("orders")