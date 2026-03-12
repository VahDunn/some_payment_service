import pytest

from app.core.domain.exceptions import NotFoundError
from app.schemas.order import OrderOut
from app.service.order_service import OrderService


@pytest.fixture
def order_service(order_repo):
    return OrderService(repo=order_repo)


@pytest.mark.asyncio
async def test_get_order_success(order_service, order_repo, order_factory):
    order = order_factory(id=1, amount="1000.00")

    order_repo.get_by_id.return_value = order

    result = await order_service.get_by_id(1)

    order_repo.get_by_id.assert_awaited_once_with(1)

    assert isinstance(result, OrderOut)
    assert result.id == order.id
    assert result.amount == order.amount


@pytest.mark.asyncio
async def test_get_order_not_found(order_service, order_repo):
    order_repo.get_by_id.return_value = None

    with pytest.raises(NotFoundError, match="Order not found"):
        await order_service.get_by_id(1)
