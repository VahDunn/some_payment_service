from fastapi import Depends

from app.external.bank.client import BankApiClient
from app.repositories.order_repo import OrderRepository
from app.repositories.payment_repo import PaymentRepository
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService
from app.api.deps.repos import get_order_repo, get_payment_repo


def get_bank_client() -> BankApiClient:
    return BankApiClient(base_url="https://bank.api")


def get_order_service(
    repo: OrderRepository = Depends(get_order_repo),
) -> OrderService:
    return OrderService(repo=repo)


def get_payment_service(
    payment_repo: PaymentRepository = Depends(get_payment_repo),
    order_repo: OrderRepository = Depends(get_order_repo),
    bank_client: BankApiClient = Depends(get_bank_client),
) -> PaymentService:
    return PaymentService(
        payment_repo=payment_repo,
        order_repo=order_repo,
        bank_client=bank_client,
    )