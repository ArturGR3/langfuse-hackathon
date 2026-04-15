# German Paperwork Assistant — Design Spec

**Date:** 2026-04-15
**Status:** Approved

---

## Overview

A mobile app that helps non-German speakers manage German paperwork. User uploads a document image from their phone; a Python FastAPI backend (running on the same laptop as Ollama) extracts text and detects PII via Gemma 4, strips PII on the server, then uses OpenAI to translate and extract actions. Results are returned to the mobile app and saved as Obsidian-compatible markdown on the laptop.

---

## Goals

- Non-German speakers can understand and act on German documents
- PII never leaves the local network unredacted (Gemma 4 runs on laptop via Ollama)
- Structured outputs for both Gemma 4 and OpenAI — no fragile JSON parsing
- Full LLM pipeline observability via Langfuse
- Prototype-ready: minimal surface area, no unnecessary features

---

## Architecture

### Pipeline

```
[Expo mobile app]
  → POST /process (multipart image upload) to FastAPI (laptop, same WiFi)
  → Gemma 4 via Ollama (structured output) → { raw_text, pii_list }
  → On-server PII scrubber → clean_text
  → OpenAI gpt-4o (structured output) → { document_type, translation, summary, actions }
  → Write markdown to local vault
  → Return JSON result to mobile app
[Expo mobile app displays result]
```

### Components

| Component | Technology | Purpose |
|---|---|---|
| Mobile app | Expo (React Native) | Image picker, display results |
| Backend | Python FastAPI | Orchestrates the full pipeline |
| OCR + PII detection | Ollama + Gemma 4 (structured output) | Extract text and identify PII |
| PII scrubber | Python string replacement | Redact PII from raw text |
| Translation + actions | OpenAI gpt-4o (structured output via Pydantic) | Translate German, extract actions |
| Observability | Langfuse Python SDK | Trace all LLM calls end-to-end |
| Vault storage | Python `pathlib` | Write Obsidian-compatible markdown |

---

## Detailed Design

### 1. Mobile App (Expo)

Thin client — two screens only:

- **Screen 1 (Home):** Image picker button. On pick, POST image as multipart/form-data to `http://<laptop-ip>:8000/process`. Show loading spinner with status text.
- **Screen 2 (Result):** Display `document_type` badge, `summary`, collapsible `translation`, and `actions` checklist. Show "Saved to vault" confirmation.

### 2. FastAPI Backend

Single endpoint:

```
POST /process
Content-Type: multipart/form-data
Body: file (image)

Response: {
  "document_type": string,
  "translation": string,
  "summary": string,
  "actions": [{ "description": string, "deadline": string | null }]
}
```

### 3. Gemma 4 Call (Ollama — Structured Output)

**Endpoint:** `POST http://localhost:11434/api/generate`

Ollama supports structured output via a `format` JSON schema field. The model is constrained to return valid JSON matching the schema.

```python
format_schema = {
    "type": "object",
    "properties": {
        "raw_text": {"type": "string"},
        "pii_list": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["raw_text", "pii_list"]
}
```

**Langfuse:** traced as generation `gemma4-ocr-pii`

### 4. On-Server PII Scrubber

Pure Python function. For each item in `pii_list`, replaces all case-insensitive occurrences in `raw_text` with `[REDACTED]`. Returns `clean_text`.

### 5. OpenAI Call (Structured Output via Pydantic)

Uses `client.beta.chat.completions.parse()` with a Pydantic model — no manual JSON parsing.

```python
class Action(BaseModel):
    description: str
    deadline: str | None

class TranslationResult(BaseModel):
    document_type: str
    translation: str
    summary: str
    actions: list[Action]
```

**Langfuse:** traced as generation `openai-translate-actions`

### 6. Markdown Vault

Written to `~/Documents/paperwork-vault/` on the laptop.

**Filename:** `YYYY-MM-DD-<document_type>.md`

```markdown
---
date: 2026-04-15
type: invoice
---

## Summary
Your electricity bill for March. Amount due: €89.50 (redacted IBAN).

## Translation
Dear Customer, please find enclosed your electricity bill for the month of March...

## Actions
- [ ] Pay bill by 2026-04-30
```

---

## Observability (Langfuse)

One trace per document, two generations:

| Generation name | Model | Input | Output |
|---|---|---|---|
| `gemma4-ocr-pii` | gemma3:4b / gemma4 | base64 image + prompt | `{ raw_text, pii_list }` |
| `openai-translate-actions` | gpt-4o | clean_text | `{ document_type, translation, summary, actions }` |

---

## Out of Scope (this prototype)

- Chat UI / RAG over vault
- True on-device Gemma 4 (phone-side inference)
- Authentication / multi-user
- Cloud sync of vault
- Camera capture (image picker only)

---

## Environment Setup

**Laptop:**
- `ollama serve` (Ollama already running, accessible at `localhost:11434`)
- `ollama pull gemma3:4b` (or `gemma4` when available)
- FastAPI server: `uvicorn main:app --host 0.0.0.0 --port 8000`
- `.env` with `OPENAI_API_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`

**Phone:**
- Expo app with `EXPO_PUBLIC_API_BASE_URL=http://<laptop-ip>:8000`
- On same WiFi network as laptop
