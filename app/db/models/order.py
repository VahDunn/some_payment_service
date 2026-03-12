from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.domain.enums import OrderPaymentStatus
from app.db.models.base import BaseORM

if TYPE_CHECKING:
    from app.db.models.payment import Payment


class Order(BaseORM):
    __tablename__ = "orders"

    amount: Mapped[Decimal] = mapped_column(sa.Numeric(12, 2), nullable=False)
    payment_status: Mapped[OrderPaymentStatus] = mapped_column(
        sa.Enum(OrderPaymentStatus, name="order_payment_status"),
        nullable=False,
        default=OrderPaymentStatus.UNPAID,
        server_default=OrderPaymentStatus.UNPAID.value,
    )

    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    __table_args__ = (sa.CheckConstraint("amount > 0", name="ck_orders_amount_gt_0"),)
