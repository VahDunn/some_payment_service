from fastapi import APIRouter, Depends

from app.api.deps.services import get_order_service
from app.schemas.order import OrderOut
from app.service.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])

order_service = Depends(get_order_service)


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: int,
    service: OrderService = order_service,
):
    return await service.get_by_id(order_id)
