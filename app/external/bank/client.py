import httpx

from app.core.domain.enums import BankPaymentStatus
from app.core.domain.exceptions import ExternalServiceError
from app.external.bank.dto import BankCheckResponse, BankStartResponse
from app.external.bank.exceptions import BankPaymentNotFoundError


class BankApiClient:
    def __init__(self, base_url: str, timeout: float = 5.0):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def acquiring_start(self, order_id: int, amount) -> BankStartResponse:
        url = f"{self._base_url}/acquiring_start"
        payload = {
            "order_id": order_id,
            "amount": str(amount),
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as e:
            raise ExternalServiceError(f"Bank API start request failed: {e}") from e

        if "error" in data:
            raise ExternalServiceError(data["error"])

        return BankStartResponse(bank_payment_id=data["bank_payment_id"])

    async def acquiring_check(self, bank_payment_id: str) -> BankCheckResponse:
        url = f"{self._base_url}/acquiring_check"
        payload = {"bank_payment_id": bank_payment_id}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as e:
            raise ExternalServiceError(f"Bank API check request failed: {e}") from e

        if data.get("error") == "payment not found":
            raise BankPaymentNotFoundError("payment not found")

        if "error" in data:
            raise ExternalServiceError(data["error"])

        return BankCheckResponse(
            bank_payment_id=data["bank_payment_id"],
            amount=data["amount"],
            status=BankPaymentStatus(data["status"]),
            paid_at=data.get("paid_at"),
        )