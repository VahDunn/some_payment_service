from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.core.domain.enums import (
    BankPaymentStatus,
    OrderPaymentStatus,
    PaymentStatus,
    PaymentType,
)
from app.db.models import Order, Payment
from app.external.bank.client import BankApiClient
from app.repo.order_repo import OrderRepository
from app.repo.payment_repo import PaymentRepository
from app.service.payment_service import PaymentService


@pytest.fixture
def payment_repo() -> AsyncMock:
    repo = AsyncMock(spec=PaymentRepository)
    repo.db = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_bank_payment_id = AsyncMock()

    async def create_side_effect(payment: Payment):
        if payment.id is None:
            payment.id = 1
        if payment.refunded_amount is None:
            payment.refunded_amount = Decimal("0.00")
        return payment

    repo.create = AsyncMock(side_effect=create_side_effect)
    return repo


@pytest.fixture
def order_repo() -> AsyncMock:
    repo = AsyncMock(spec=OrderRepository)
    repo.get_by_id = AsyncMock()
    repo.get_paid_total = AsyncMock()
    repo.refresh_payment_status = AsyncMock()
    return repo


@pytest.fixture
def bank_client() -> AsyncMock:
    client = AsyncMock(spec=BankApiClient)
    client.acquiring_start = AsyncMock()
    client.acquiring_check = AsyncMock()
    return client


@pytest.fixture
def payment_service(
    payment_repo: AsyncMock,
    order_repo: AsyncMock,
    bank_client: AsyncMock,
) -> PaymentService:
    return PaymentService(
        payment_repo=payment_repo,
        order_repo=order_repo,
        bank_client=bank_client,
    )


@pytest.fixture
def order_factory():
    def factory(
        *,
        id: int = 1,
        amount: str = "1000.00",
        payment_status: OrderPaymentStatus = OrderPaymentStatus.UNPAID,
    ) -> Order:
        return Order(
            id=id,
            amount=Decimal(amount),
            payment_status=payment_status,
        )

    return factory


@pytest.fixture
def payment_factory():
    def factory(
        *,
        id: int = 1,
        order_id: int = 1,
        amount: str = "100.00",
        type: PaymentType = PaymentType.CASH,
        status: PaymentStatus = PaymentStatus.PENDING,
        refunded_amount: str = "0.00",
        bank_payment_id: str | None = None,
        bank_status: BankPaymentStatus | None = None,
    ) -> Payment:
        return Payment(
            id=id,
            order_id=order_id,
            amount=Decimal(amount),
            type=type,
            status=status,
            refunded_amount=Decimal(refunded_amount),
            bank_payment_id=bank_payment_id,
            bank_status=bank_status,
        )

    return factory
