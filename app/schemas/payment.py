from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.core.domain.enums import BankPaymentStatus, PaymentStatus, PaymentType


class PaymentCreateParams(BaseModel):
    order_id: int
    amount: Decimal = Field(gt=0)
    type: PaymentType


class PaymentRefundParams(BaseModel):
    amount: Decimal = Field(gt=0)


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    amount: Decimal
    type: PaymentType
    status: PaymentStatus
    bank_payment_id: str | None
    bank_status: BankPaymentStatus | None
    bank_paid_at: datetime | None
    bank_error: str | None
    refunded_amount: Decimal