from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.core.domain.enums import BankPaymentStatus
from app.core.domain.exceptions import ExternalServiceError
from app.external.bank.client import BankApiClient
from app.external.bank.exceptions import BankPaymentNotFoundError


@pytest.mark.asyncio
async def test_acquiring_start_success():
    client = BankApiClient(base_url="https://bank.api")

    response_data = {
        "bank_payment_id": "bank-123"
    }

    mock_response = Mock()
    mock_response.json.return_value = response_data
    mock_response.raise_for_status.return_value = None

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=mock_response)):
        result = await client.acquiring_start(order_id=1, amount=Decimal("500.00"))

    assert result.bank_payment_id == "bank-123"


@pytest.mark.asyncio
async def test_acquiring_start_bank_error():
    client = BankApiClient(base_url="https://bank.api")

    response_data = {
        "error": "payment creation failed"
    }

    mock_response = Mock()
    mock_response.json.return_value = response_data
    mock_response.raise_for_status.return_value = None

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=mock_response)):
        with pytest.raises(ExternalServiceError, match="payment creation failed"):
            await client.acquiring_start(order_id=1, amount=100)


@pytest.mark.asyncio
async def test_acquiring_check_success():
    client = BankApiClient(base_url="https://bank.api")

    response_data = {
        "bank_payment_id": "bank-123",
        "amount": "500.00",
        "status": "paid",
        "paid_at": None,
    }

    mock_response = Mock()
    mock_response.json.return_value = response_data
    mock_response.raise_for_status.return_value = None

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=mock_response)):
        result = await client.acquiring_check("bank-123")

    assert result.bank_payment_id == "bank-123"
    assert result.amount == Decimal("500.00")
    assert result.status == BankPaymentStatus.PAID


@pytest.mark.asyncio
async def test_acquiring_check_payment_not_found():
    client = BankApiClient(base_url="https://bank.api")

    response_data = {
        "error": "payment not found"
    }

    mock_response = Mock()
    mock_response.json.return_value = response_data
    mock_response.raise_for_status.return_value = None

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=mock_response)):
        with pytest.raises(BankPaymentNotFoundError, match="payment not found"):
            await client.acquiring_check("bank-123")