# backend/services/openai_service.py
import os
from langfuse.openai import OpenAI   # langfuse drop-in wrapper for auto-tracing
from models import TranslationResult

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "dummy-key-for-testing"))

SYSTEM_PROMPT = """You are a document processing assistant for non-German speakers living in Germany.
The user will provide text extracted from a German document. PII has already been redacted as [REDACTED].
Translate the document to English and extract actionable items."""

USER_TEMPLATE = """Document:
{clean_text}"""


async def call_openai(clean_text: str) -> TranslationResult:
    response = openai_client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_TEMPLATE.format(clean_text=clean_text)},
        ],
        response_format=TranslationResult,
    )
    return response.choices[0].message.parsed
