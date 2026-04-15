import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.ollama import call_gemma4


@pytest.mark.asyncio
async def test_returns_parsed_result():
    mock_body = json.dumps({
        "raw_text": "Rechnung Nr. 123",
        "pii_list": ["Max Mustermann"],
    })
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(return_value={"response": mock_body})

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        result = await call_gemma4("base64data")

    assert result.raw_text == "Rechnung Nr. 123"
    assert result.pii_list == ["Max Mustermann"]


@pytest.mark.asyncio
async def test_raises_on_http_error():
    import httpx
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "500", request=MagicMock(), response=MagicMock()
            )
        )
        mock_client_cls.return_value = mock_client

        with pytest.raises(httpx.HTTPStatusError):
            await call_gemma4("base64data")
