from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.db import get_db
from app.repositories.order_repo import OrderRepository
from app.repositories.payment_repo import PaymentRepository


def get_order_repo(db: AsyncSession = Depends(get_db)) -> OrderRepository:
    return OrderRepository(db)


def get_payment_repo(db: AsyncSession = Depends(get_db)) -> PaymentRepository:
    return PaymentRepository(db)