import asyncio
from decimal import Decimal

from sqlalchemy import select

from app.core.domain.enums import OrderPaymentStatus
from app.db.engine import SessionLocal
from app.db.models import Order


async def seed_orders():
    async with SessionLocal() as session:
        existing = await session.execute(select(Order.id))
        if existing.scalars().first():
            print("Orders already exist. Skip seeding.")
            return

        orders = [
            Order(
                amount=Decimal("1000.00"),
                payment_status=OrderPaymentStatus.UNPAID,
            ),
            Order(
                amount=Decimal("1500.00"),
                payment_status=OrderPaymentStatus.UNPAID,
            ),
            Order(
                amount=Decimal("700.00"),
                payment_status=OrderPaymentStatus.UNPAID,
            ),
        ]

        session.add_all(orders)
        await session.commit()

        print("Seed completed: created 3 orders")


async def main():
    await seed_orders()


if __name__ == "__main__":
    asyncio.run(main())
