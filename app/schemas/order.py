from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.core.domain.enums import OrderPaymentStatus


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    payment_status: OrderPaymentStatus