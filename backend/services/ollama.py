import os
import httpx
from models import OcrPiiResult

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL = "gemma3:4b"  # switch to gemma4 when available in Ollama

PROMPT = """You are a document processing assistant. Given this document image:
1. Extract all visible text exactly as written.
2. Identify all PII: full names, addresses, IBANs, tax IDs, dates of birth, phone numbers, email addresses.

Return only valid JSON matching the provided schema."""

FORMAT_SCHEMA = {
    "type": "object",
    "properties": {
        "raw_text": {"type": "string"},
        "pii_list": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["raw_text", "pii_list"],
}


async def call_gemma4(image_base64: str) -> OcrPiiResult:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": MODEL,
                "prompt": PROMPT,
                "images": [image_base64],
                "stream": False,
                "format": FORMAT_SCHEMA,
            },
        )
        response.raise_for_status()
        data = response.json()
        return OcrPiiResult.model_validate_json(data["response"])
