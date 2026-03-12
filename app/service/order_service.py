from app.core.domain.exceptions import NotFoundError
from app.repo.order_repo import OrderRepository
from app.schemas.order import OrderOut


class OrderService:
    def __init__(self, repo: OrderRepository):
        self._repo = repo

    async def get_by_id(self, order_id: int) -> OrderOut:
        order = await self._repo.get_by_id(order_id)
        if not order:
            raise NotFoundError("Order not found")
        return OrderOut.model_validate(order, from_attributes=True)