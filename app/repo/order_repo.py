from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.domain.enums import OrderPaymentStatus, PaymentStatus
from app.db.models import Order, Payment


class OrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, order_id: int) -> Order | None:
        stmt = (
            sa.select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.payments))
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_paid_total(self, order_id: int) -> Decimal:
        stmt = sa.select(
            sa.func.coalesce(
                sa.func.sum(Payment.amount - Payment.refunded_amount),
                0,
            )
        ).where(
            Payment.order_id == order_id,
            Payment.status.in_([PaymentStatus.SUCCEEDED, PaymentStatus.REFUNDED]),
        )
        res = await self.db.execute(stmt)
        return res.scalar_one()

    async def refresh_payment_status(self, order: Order) -> Order:
        paid_total = await self.get_paid_total(order.id)

        if paid_total <= 0:
            order.payment_status = OrderPaymentStatus.UNPAID
        elif paid_total < order.amount:
            order.payment_status = OrderPaymentStatus.PARTIALLY_PAID
        else:
            order.payment_status = OrderPaymentStatus.PAID

        await self.db.flush()
        return order