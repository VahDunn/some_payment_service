from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.core.domain.enums import BankPaymentStatus


class BankStartResponse(BaseModel):
    bank_payment_id: str


class BankCheckResponse(BaseModel):
    bank_payment_id: str
    amount: Decimal
    status: BankPaymentStatus
    paid_at: datetime | None = None
