from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.domain.enums import BankPaymentStatus, PaymentStatus, PaymentType
from app.db.models.base import BaseORM

if TYPE_CHECKING:
    from app.db.models.order import Order


class Payment(BaseORM):
    __tablename__ = "payments"

    order_id: Mapped[int] = mapped_column(
        sa.ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(sa.Numeric(12, 2), nullable=False)

    type: Mapped[PaymentType] = mapped_column(
        sa.Enum(PaymentType, name="payment_type"),
        nullable=False,
    )
    status: Mapped[PaymentStatus] = mapped_column(
        sa.Enum(PaymentStatus, name="payment_status"),
        nullable=False,
        default=PaymentStatus.PENDING,
        server_default=PaymentStatus.PENDING.value,
    )

    # данные для эквайринга
    bank_payment_id: Mapped[str | None] = mapped_column(sa.String(128), nullable=True, unique=True)
    bank_status: Mapped[BankPaymentStatus | None] = mapped_column(
        sa.Enum(BankPaymentStatus, name="bank_payment_status"),
        nullable=True,
    )
    bank_paid_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    bank_error: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    refunded_amount: Mapped[Decimal] = mapped_column(
        sa.Numeric(12, 2),
        nullable=False,
        default=0,
        server_default="0",
    )

    order: Mapped["Order"] = relationship("Order", back_populates="payments")

    __table_args__ = (
        sa.CheckConstraint("amount > 0", name="ck_payments_amount_gt_0"),
        sa.CheckConstraint("refunded_amount >= 0", name="ck_payments_refunded_amount_gte_0"),
        sa.CheckConstraint("refunded_amount <= amount", name="ck_payments_refunded_amount_lte_amount"),
    )