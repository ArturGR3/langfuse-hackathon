# backend/tests/test_openai_service.py
import pytest
from unittest.mock import MagicMock, patch
from services.openai_service import call_openai
from models import TranslationResult, Action


@pytest.mark.asyncio
async def test_returns_translation_result():
    mock_result = TranslationResult(
        document_type="invoice",
        translation="Dear customer, your bill is due.",
        summary="Electricity bill due April 30.",
        actions=[Action(description="Pay €89.50", deadline="2026-04-30")],
    )

    mock_parsed = MagicMock()
    mock_parsed.choices[0].message.parsed = mock_result

    with patch("services.openai_service.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse.return_value = mock_parsed
        result = await call_openai("Strom Rechnung text here")

    assert result.document_type == "invoice"
    assert result.translation == "Dear customer, your bill is due."
    assert len(result.actions) == 1
    assert result.actions[0].deadline == "2026-04-30"
