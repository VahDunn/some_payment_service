from decimal import Decimal

from app.core.domain.enums import BankPaymentStatus, PaymentStatus, PaymentType
from app.core.domain.exceptions import ConflictError, NotFoundError, ValidationError
from app.db.models import Payment
from app.external.bank.client import BankApiClient
from app.external.bank.exceptions import BankPaymentNotFoundError
from app.repo.order_repo import OrderRepository
from app.repo.payment_repo import PaymentRepository
from app.schemas.payment import PaymentCreateParams, PaymentOut


class PaymentService:
    def __init__(
        self,
        payment_repo: PaymentRepository,
        order_repo: OrderRepository,
        bank_client: BankApiClient,
    ):
        self._payment_repo = payment_repo
        self._order_repo = order_repo
        self._bank_client = bank_client

    async def create(self, payload: PaymentCreateParams) -> PaymentOut:
        order = await self._order_repo.get_by_id(payload.order_id)
        if not order:
            raise NotFoundError("Order not found")

        paid_total = await self._order_repo.get_paid_total(order.id)
        available_to_pay = order.amount - paid_total

        if payload.amount > available_to_pay:
            raise ValidationError(
                f"Payment amount exceeds order остаток. Available: {available_to_pay}"
            )

        payment = Payment(
            order_id=payload.order_id,
            amount=payload.amount,
            type=payload.type,
            status=PaymentStatus.PENDING,
        )

        if payload.type == PaymentType.CASH:
            payment.status = PaymentStatus.SUCCEEDED
            await self._payment_repo.create(payment)
            await self._order_repo.refresh_payment_status(order)
            await self._payment_repo.db.commit()
            return PaymentOut.model_validate(payment, from_attributes=True)

        # acquiring
        bank_response = await self._bank_client.acquiring_start(
            order_id=payload.order_id,
            amount=payload.amount,
        )
        payment.bank_payment_id = bank_response.bank_payment_id
        payment.bank_status = BankPaymentStatus.NEW

        await self._payment_repo.create(payment)
        await self._payment_repo.db.commit()

        return PaymentOut.model_validate(payment, from_attributes=True)

    async def refund(self, payment_id: int, amount: Decimal) -> PaymentOut:
        payment = await self._payment_repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundError("Payment not found")

        if payment.status not in [PaymentStatus.SUCCEEDED, PaymentStatus.REFUNDED]:
            raise ConflictError("Only succeeded/refunded payments can be refunded")

        available_for_refund = payment.amount - payment.refunded_amount
        if amount > available_for_refund:
            raise ValidationError(
                f"Refund amount exceeds available refund amount: {available_for_refund}"
            )

        payment.refunded_amount += amount
        payment.status = (
            PaymentStatus.REFUNDED
            if payment.refunded_amount > 0
            else PaymentStatus.SUCCEEDED
        )

        order = await self._order_repo.get_by_id(payment.order_id)
        await self._order_repo.refresh_payment_status(order)
        await self._payment_repo.db.commit()

        return PaymentOut.model_validate(payment, from_attributes=True)

    async def sync_acquiring_payment(self, payment_id: int) -> PaymentOut:
        payment = await self._payment_repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundError("Payment not found")

        if payment.type != PaymentType.ACQUIRING:
            raise ConflictError("Sync is available only for acquiring payments")

        if not payment.bank_payment_id:
            raise ConflictError("Bank payment id is missing")

        try:
            bank_state = await self._bank_client.acquiring_check(payment.bank_payment_id)
        except BankPaymentNotFoundError:
            payment.bank_status = BankPaymentStatus.UNKNOWN
            payment.bank_error = "payment not found in bank"
            await self._payment_repo.db.commit()
            return PaymentOut.model_validate(payment, from_attributes=True)

        payment.bank_status = bank_state.status
        payment.bank_paid_at = bank_state.paid_at
        payment.bank_error = None

        if bank_state.status == BankPaymentStatus.PAID:
            payment.status = PaymentStatus.SUCCEEDED
        elif bank_state.status == BankPaymentStatus.FAILED:
            payment.status = PaymentStatus.FAILED
        else:
            payment.status = PaymentStatus.PENDING

        order = await self._order_repo.get_by_id(payment.order_id)
        await self._order_repo.refresh_payment_status(order)
        await self._payment_repo.db.commit()

        return PaymentOut.model_validate(payment, from_attributes=True)