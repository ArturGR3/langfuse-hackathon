# German Paperwork Assistant

A privacy-first mobile app that helps non-German speakers understand and act on official German documents — without exposing sensitive personal data to cloud AI services.

---

## The Problem

Germany is notorious for bureaucracy. Official correspondence arrives as dense, formal German: tax notices, health insurance letters, utility bills, landlord letters, registration forms. For expats and immigrants, this creates a compounding problem:

- **Language barrier** — legal and administrative German is difficult even for fluent speakers
- **High stakes** — missed deadlines or incorrect responses carry real consequences (fines, contract renewals, legal liability)
- **Data sensitivity** — these documents contain tax IDs, IBANs, insurance numbers, and personal details that shouldn't be sent to a third-party AI service without protection

Existing solutions (Google Translate, ChatGPT) either don't understand document context or require uploading raw personal data to the cloud.

---

## The Solution

Take a photo of the document. Get back:

- A plain-English **summary** of what the document is and why it matters
- A full **translation**
- An **action checklist** with deadlines ("Pay €89.50 by April 30")
- Automatic archival to a **local Obsidian vault** for future reference

All with a privacy architecture that ensures sensitive personal data never leaves your device unredacted.

---

## Architecture

The system is built around a single insight: **OCR and PII detection can run locally; translation does not need to see your personal data**.

```
┌─────────────────────────────────────────────┐
│           Expo Mobile App (iOS/Android)      │
│   Photo library → Upload → Display results  │
└───────────────────┬─────────────────────────┘
                    │ POST /process (image)
                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (runs on laptop)                  │
│                                                                      │
│  Step 1 ── Gemma 3 via Ollama (LOCAL, never leaves your machine)    │
│            ├─ Extracts raw text from the document image             │
│            └─ Identifies PII: names, IBANs, tax IDs, etc.          │
│                                                                      │
│  Step 2 ── PII Scrubber (on-server, before any network call)        │
│            └─ Replaces all identified PII with [REDACTED]           │
│                                                                      │
│  Step 3 ── GPT-4o via OpenAI API (cloud, receives only clean text) │
│            ├─ Translates German → English                           │
│            ├─ Classifies document type                              │
│            ├─ Writes executive summary                              │
│            └─ Extracts action items with deadlines                  │
│                                                                      │
│  Step 4 ── Vault Writer                                              │
│            └─ Saves Obsidian-compatible markdown to ~/Documents/    │
│                                                                      │
│  All steps traced end-to-end via Langfuse                           │
└───────────────────┬─────────────────────────────────────────────────┘
                    │ JSON (summary, translation, actions)
                    ↓
         Mobile app displays results
```

### Privacy Boundary

| Data | Where it goes |
|---|---|
| Raw document image | Your laptop only |
| Extracted text + PII list | Your laptop only (Ollama/Gemma, local) |
| Redacted text `[REDACTED]` | OpenAI API (cloud) |
| Translation & action items | Back to your phone |
| Full processed document | Local vault (`~/Documents/paperwork-vault/`) |
| Trace metadata (no PII) | Langfuse Cloud (observability) |

OpenAI and Langfuse receive **zero personally identifiable information**.

---

## Tech Stack

**Backend**
- FastAPI + Python 3.11
- Ollama (local inference) running Gemma 3:4b — OCR and PII detection
- OpenAI GPT-4o — translation and action extraction, via structured outputs (Pydantic)
- Langfuse — end-to-end LLM observability and tracing

**Mobile**
- Expo (React Native) — iOS and Android
- Expo Router — file-based navigation
- TypeScript

**Storage**
- Local filesystem — Obsidian-compatible markdown vault

---

## Observability with Langfuse

Every document processed generates a Langfuse trace with two generations:

1. `gemma3-ocr-pii` — the local OCR+PII extraction step (input: image, output: raw text + PII list)
2. `openai-translate-actions` — the cloud translation step (input: redacted text, output: structured result)

This gives full visibility into latency, token usage, and output quality across the pipeline — without ever logging sensitive user data.

---

## Repository Structure

```
langfuse-hackathon/
├── backend/
│   ├── main.py                  # FastAPI app, /process endpoint
│   ├── models.py                # Pydantic models
│   ├── services/
│   │   ├── ollama.py            # Gemma OCR + PII via Ollama
│   │   ├── openai_service.py    # GPT-4o translation + actions
│   │   ├── scrubber.py          # PII redaction
│   │   └── vault.py             # Obsidian markdown writer
│   └── tests/
├── mobile/
│   ├── app/
│   │   ├── index.tsx            # Home screen (image upload)
│   │   └── result.tsx           # Results screen
│   └── src/types.ts             # Shared TypeScript types
└── docs/
    └── superpowers/
        ├── specs/               # Design spec
        └── plans/               # Implementation plan
```

---

## Running Locally

**Prerequisites:** Ollama installed, `gemma3:4b` pulled, OpenAI API key, Langfuse account.

```bash
# Start Ollama (accessible on your local network)
OLLAMA_HOST=0.0.0.0 ollama serve

# Backend
cd backend
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8000

# Mobile (phone and laptop on same WiFi)
cd mobile
# Set EXPO_PUBLIC_API_BASE_URL=http://<your-laptop-ip>:8000 in .env
npm install
npx expo start
```
