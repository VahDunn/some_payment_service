from fastapi import APIRouter, Depends, status

from app.api.deps.services import get_payment_service
from app.schemas.payment import PaymentCreateParams, PaymentOut, PaymentRefundParams
from app.service.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])

payment_service = Depends(get_payment_service)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PaymentOut)
async def create_payment(
    params: PaymentCreateParams,
    service: PaymentService = payment_service,
):
    return await service.create(params)


@router.post("/{payment_id}/refund", response_model=PaymentOut)
async def refund_payment(
    payment_id: int,
    params: PaymentRefundParams,
    service: PaymentService = payment_service,
):
    return await service.refund(payment_id=payment_id, amount=params.amount)


@router.post("/{payment_id}/sync", response_model=PaymentOut)
async def sync_payment(
    payment_id: int,
    service: PaymentService = payment_service,
):
    return await service.sync_acquiring_payment(payment_id=payment_id)
