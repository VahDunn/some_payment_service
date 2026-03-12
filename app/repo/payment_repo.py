import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Payment


class PaymentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payment: Payment) -> Payment:
        self.db.add(payment)
        await self.db.flush()
        return payment

    async def get_by_id(self, payment_id: int) -> Payment | None:
        stmt = sa.select(Payment).where(Payment.id == payment_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_bank_payment_id(self, bank_payment_id: str) -> Payment | None:
        stmt = sa.select(Payment).where(Payment.bank_payment_id == bank_payment_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()
