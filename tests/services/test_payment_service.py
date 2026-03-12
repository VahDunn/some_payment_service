from decimal import Decimal

import pytest

from app.core.domain.enums import BankPaymentStatus, PaymentStatus, PaymentType
from app.core.domain.exceptions import ConflictError, NotFoundError, ValidationError
from app.external.bank.dto import BankCheckResponse, BankStartResponse
from app.external.bank.exceptions import BankPaymentNotFoundError
from app.schemas.payment import PaymentCreateParams


@pytest.mark.asyncio
async def test_create_cash_payment_success(
    payment_service,
    order_repo,
    payment_repo,
    order_factory,
):
    order = order_factory(amount="1000.00")
    order_repo.get_by_id.return_value = order
    order_repo.get_paid_total.return_value = Decimal("200.00")

    payload = PaymentCreateParams(
        order_id=order.id,
        amount=Decimal("300.00"),
        type=PaymentType.CASH,
    )

    result = await payment_service.create(payload)

    payment_repo.create.assert_awaited_once()
    order_repo.refresh_payment_status.assert_awaited_once_with(order)
    payment_repo.db.commit.assert_awaited_once()

    created_payment = payment_repo.create.await_args.args[0]
    assert created_payment.order_id == order.id
    assert created_payment.amount == Decimal("300.00")
    assert created_payment.type == PaymentType.CASH
    assert created_payment.status == PaymentStatus.SUCCEEDED

    assert result.order_id == order.id
    assert result.amount == Decimal("300.00")
    assert result.type == PaymentType.CASH
    assert result.status == PaymentStatus.SUCCEEDED


@pytest.mark.asyncio
async def test_create_acquiring_payment_success(
    payment_service,
    order_repo,
    payment_repo,
    bank_client,
    order_factory,
):
    order = order_factory(amount="1000.00")
    order_repo.get_by_id.return_value = order
    order_repo.get_paid_total.return_value = Decimal("100.00")
    bank_client.acquiring_start.return_value = BankStartResponse(
        bank_payment_id="bank-123",
    )

    payload = PaymentCreateParams(
        order_id=order.id,
        amount=Decimal("500.00"),
        type=PaymentType.ACQUIRING,
    )

    result = await payment_service.create(payload)

    bank_client.acquiring_start.assert_awaited_once_with(
        order_id=order.id,
        amount=Decimal("500.00"),
    )
    payment_repo.create.assert_awaited_once()
    payment_repo.db.commit.assert_awaited_once()
    order_repo.refresh_payment_status.assert_not_awaited()

    created_payment = payment_repo.create.await_args.args[0]
    assert created_payment.order_id == order.id
    assert created_payment.amount == Decimal("500.00")
    assert created_payment.type == PaymentType.ACQUIRING
    assert created_payment.status == PaymentStatus.PENDING
    assert created_payment.bank_payment_id == "bank-123"
    assert created_payment.bank_status == BankPaymentStatus.NEW

    assert result.order_id == order.id
    assert result.amount == Decimal("500.00")
    assert result.type == PaymentType.ACQUIRING
    assert result.status == PaymentStatus.PENDING
    assert result.bank_payment_id == "bank-123"
    assert result.bank_status == BankPaymentStatus.NEW


@pytest.mark.asyncio
async def test_create_payment_order_not_found(
    payment_service,
    order_repo,
):
    order_repo.get_by_id.return_value = None

    payload = PaymentCreateParams(
        order_id=999,
        amount=Decimal("100.00"),
        type=PaymentType.CASH,
    )

    with pytest.raises(NotFoundError, match="Order not found"):
        await payment_service.create(payload)


@pytest.mark.asyncio
async def test_create_payment_amount_exceeds_order_remainder(
    payment_service,
    order_repo,
    order_factory,
):
    order = order_factory(amount="1000.00")
    order_repo.get_by_id.return_value = order
    order_repo.get_paid_total.return_value = Decimal("900.00")

    payload = PaymentCreateParams(
        order_id=order.id,
        amount=Decimal("200.00"),
        type=PaymentType.CASH,
    )

    with pytest.raises(ValidationError, match="Payment amount exceeds order остаток"):
        await payment_service.create(payload)


@pytest.mark.asyncio
async def test_refund_payment_success_partial_refund(
    payment_service,
    payment_repo,
    order_repo,
    payment_factory,
    order_factory,
):
    payment = payment_factory(
        id=10,
        order_id=1,
        amount="500.00",
        type=PaymentType.CASH,
        status=PaymentStatus.SUCCEEDED,
        refunded_amount="0.00",
    )
    order = order_factory(id=1, amount="1000.00")

    payment_repo.get_by_id.return_value = payment
    order_repo.get_by_id.return_value = order

    result = await payment_service.refund(payment_id=10, amount=Decimal("100.00"))

    assert payment.refunded_amount == Decimal("100.00")
    assert payment.status == PaymentStatus.REFUNDED

    order_repo.refresh_payment_status.assert_awaited_once_with(order)
    payment_repo.db.commit.assert_awaited_once()

    assert result.id == 10
    assert result.refunded_amount == Decimal("100.00")
    assert result.status == PaymentStatus.REFUNDED


@pytest.mark.asyncio
async def test_refund_payment_not_found(
    payment_service,
    payment_repo,
):
    payment_repo.get_by_id.return_value = None

    with pytest.raises(NotFoundError, match="Payment not found"):
        await payment_service.refund(payment_id=999, amount=Decimal("50.00"))


@pytest.mark.asyncio
async def test_refund_payment_invalid_status(
    payment_service,
    payment_repo,
    payment_factory,
):
    payment = payment_factory(
        id=10,
        order_id=1,
        amount="500.00",
        type=PaymentType.ACQUIRING,
        status=PaymentStatus.PENDING,
    )
    payment_repo.get_by_id.return_value = payment

    with pytest.raises(
        ConflictError, match="Only succeeded/refunded payments can be refunded"
    ):
        await payment_service.refund(payment_id=10, amount=Decimal("50.00"))


@pytest.mark.asyncio
async def test_refund_payment_amount_exceeds_available_refund(
    payment_service,
    payment_repo,
    payment_factory,
):
    payment = payment_factory(
        id=10,
        order_id=1,
        amount="500.00",
        type=PaymentType.CASH,
        status=PaymentStatus.SUCCEEDED,
        refunded_amount="450.00",
    )
    payment_repo.get_by_id.return_value = payment

    with pytest.raises(
        ValidationError, match="Refund amount exceeds available refund amount"
    ):
        await payment_service.refund(payment_id=10, amount=Decimal("100.00"))


@pytest.mark.asyncio
async def test_sync_acquiring_payment_paid(
    payment_service,
    payment_repo,
    order_repo,
    bank_client,
    payment_factory,
    order_factory,
):
    payment = payment_factory(
        id=11,
        order_id=1,
        amount="500.00",
        type=PaymentType.ACQUIRING,
        status=PaymentStatus.PENDING,
        bank_payment_id="bank-123",
        bank_status=BankPaymentStatus.NEW,
    )
    order = order_factory(id=1, amount="1000.00")

    payment_repo.get_by_id.return_value = payment
    order_repo.get_by_id.return_value = order
    bank_client.acquiring_check.return_value = BankCheckResponse(
        bank_payment_id="bank-123",
        amount=Decimal("500.00"),
        status=BankPaymentStatus.PAID,
        paid_at=None,
    )

    result = await payment_service.sync_acquiring_payment(payment_id=11)

    bank_client.acquiring_check.assert_awaited_once_with("bank-123")
    order_repo.refresh_payment_status.assert_awaited_once_with(order)
    payment_repo.db.commit.assert_awaited_once()

    assert payment.bank_status == BankPaymentStatus.PAID
    assert payment.status == PaymentStatus.SUCCEEDED
    assert result.status == PaymentStatus.SUCCEEDED
    assert result.bank_status == BankPaymentStatus.PAID


@pytest.mark.asyncio
async def test_sync_acquiring_payment_failed(
    payment_service,
    payment_repo,
    order_repo,
    bank_client,
    payment_factory,
    order_factory,
):
    payment = payment_factory(
        id=11,
        order_id=1,
        amount="500.00",
        type=PaymentType.ACQUIRING,
        status=PaymentStatus.PENDING,
        bank_payment_id="bank-123",
        bank_status=BankPaymentStatus.NEW,
    )
    order = order_factory(id=1, amount="1000.00")

    payment_repo.get_by_id.return_value = payment
    order_repo.get_by_id.return_value = order
    bank_client.acquiring_check.return_value = BankCheckResponse(
        bank_payment_id="bank-123",
        amount=Decimal("500.00"),
        status=BankPaymentStatus.FAILED,
        paid_at=None,
    )

    result = await payment_service.sync_acquiring_payment(payment_id=11)

    assert payment.bank_status == BankPaymentStatus.FAILED
    assert payment.status == PaymentStatus.FAILED
    assert result.status == PaymentStatus.FAILED
    assert result.bank_status == BankPaymentStatus.FAILED


@pytest.mark.asyncio
async def test_sync_acquiring_payment_not_found(
    payment_service,
    payment_repo,
):
    payment_repo.get_by_id.return_value = None

    with pytest.raises(NotFoundError, match="Payment not found"):
        await payment_service.sync_acquiring_payment(payment_id=999)


@pytest.mark.asyncio
async def test_sync_acquiring_payment_for_cash_forbidden(
    payment_service,
    payment_repo,
    payment_factory,
):
    payment = payment_factory(
        id=10,
        order_id=1,
        amount="300.00",
        type=PaymentType.CASH,
        status=PaymentStatus.SUCCEEDED,
    )
    payment_repo.get_by_id.return_value = payment

    with pytest.raises(
        ConflictError, match="Sync is available only for acquiring payments"
    ):
        await payment_service.sync_acquiring_payment(payment_id=10)


@pytest.mark.asyncio
async def test_sync_acquiring_payment_without_bank_payment_id_forbidden(
    payment_service,
    payment_repo,
    payment_factory,
):
    payment = payment_factory(
        id=10,
        order_id=1,
        amount="300.00",
        type=PaymentType.ACQUIRING,
        status=PaymentStatus.PENDING,
        bank_payment_id=None,
    )
    payment_repo.get_by_id.return_value = payment

    with pytest.raises(ConflictError, match="Bank payment id is missing"):
        await payment_service.sync_acquiring_payment(payment_id=10)


@pytest.mark.asyncio
async def test_sync_acquiring_payment_not_found_in_bank(
    payment_service,
    payment_repo,
    bank_client,
    payment_factory,
):
    payment = payment_factory(
        id=11,
        order_id=1,
        amount="500.00",
        type=PaymentType.ACQUIRING,
        status=PaymentStatus.PENDING,
        bank_payment_id="bank-404",
        bank_status=BankPaymentStatus.NEW,
    )
    payment_repo.get_by_id.return_value = payment
    bank_client.acquiring_check.side_effect = BankPaymentNotFoundError(
        "payment not found"
    )

    result = await payment_service.sync_acquiring_payment(payment_id=11)

    assert payment.bank_status == BankPaymentStatus.UNKNOWN
    assert payment.bank_error == "payment not found in bank"
    payment_repo.db.commit.assert_awaited_once()

    assert result.bank_status == BankPaymentStatus.UNKNOWN
    assert result.bank_error == "payment not found in bank"
