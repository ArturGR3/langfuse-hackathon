# backend/models.py
from pydantic import BaseModel


class OcrPiiResult(BaseModel):
    raw_text: str
    pii_list: list[str]


class Action(BaseModel):
    description: str
    deadline: str | None


class TranslationResult(BaseModel):
    document_type: str
    translation: str
    summary: str
    actions: list[Action]
