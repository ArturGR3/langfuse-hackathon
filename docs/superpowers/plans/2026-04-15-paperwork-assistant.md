# German Paperwork Assistant — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python FastAPI backend + Expo mobile app that lets users upload a German document image, extract text and detect PII via Gemma 4 (Ollama), redact PII, translate and extract actions via OpenAI, and save results as Obsidian-compatible markdown — with Langfuse tracing throughout.

**Architecture:** Expo picks an image and POSTs it to FastAPI. FastAPI calls Ollama/Gemma 4 with structured output (JSON schema) to get `raw_text` + `pii_list`, scrubs PII on-server, calls OpenAI with structured output (Pydantic) to get translation + actions, writes markdown to `~/Documents/paperwork-vault/`, and returns JSON to the mobile app. All LLM calls are traced in Langfuse using the `@observe` decorator and the Langfuse OpenAI drop-in wrapper.

**Tech Stack:** Python 3.11+, FastAPI, httpx, openai, langfuse, pydantic, python-dotenv, pytest; Expo SDK 52, expo-image-picker, TypeScript

---

## File Structure

```
langfuse-hackathon/
├── backend/
│   ├── main.py                  ← FastAPI app, single /process endpoint
│   ├── models.py                ← Pydantic models (OcrPiiResult, TranslationResult, Action)
│   ├── services/
│   │   ├── ollama.py            ← Gemma 4 call (structured output via JSON schema)
│   │   ├── scrubber.py          ← PII redaction (pure function)
│   │   ├── openai_service.py    ← OpenAI translation + action extraction
│   │   └── vault.py             ← Write markdown to ~/Documents/paperwork-vault/
│   ├── .env.example
│   ├── requirements.txt
│   └── tests/
│       ├── test_scrubber.py
│       ├── test_ollama.py
│       └── test_openai_service.py
└── mobile/
    ├── app/
    │   ├── _layout.tsx          ← Expo Router root layout
    │   ├── index.tsx            ← Home screen (image picker + POST to backend)
    │   └── result.tsx           ← Result screen (summary, translation, actions)
    ├── src/types.ts             ← Shared TypeScript types
    ├── package.json
    ├── app.json
    └── .env.example
```

---

## Task 1: Bootstrap Python Backend

**Files:**
- Create: `backend/pyproject.toml` (via uv init)
- Create: `backend/.env.example`
- Create: `backend/main.py`

- [ ] **Step 1: Create backend directory and init uv project**

```bash
mkdir -p backend/services backend/tests
cd backend
uv init --no-readme
uv add fastapi uvicorn httpx openai "langfuse>=2.53.0" pydantic python-dotenv python-multipart
uv add --dev pytest pytest-asyncio
```

- [ ] **Step 2: Create .env.example**

```bash
cat > .env.example << 'EOF'
OPENAI_API_KEY=sk-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
OLLAMA_BASE_URL=http://localhost:11434
EOF
cp .env.example .env
```

Fill in real values in `backend/.env`.

- [ ] **Step 4: Create minimal FastAPI app**

```python
# backend/main.py
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Paperwork Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 4: Verify server starts**

```bash
cd backend
uv run uvicorn main:app --reload
```

Expected: `Uvicorn running on http://127.0.0.1:8000`. Ctrl+C to stop.

Visit `http://localhost:8000/health` → `{"status": "ok"}`

- [ ] **Step 6: Commit**

```bash
git init  # if not already done at repo root
git add backend/
git commit -m "feat: bootstrap FastAPI backend"
```

---

## Task 2: Define Pydantic Models

**Files:**
- Create: `backend/models.py`

- [ ] **Step 1: Create models**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add backend/models.py
git commit -m "feat: add Pydantic models"
```

---

## Task 3: Implement & Test PII Scrubber

**Files:**
- Create: `backend/services/scrubber.py`
- Create: `backend/tests/test_scrubber.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_scrubber.py
from services.scrubber import scrub_pii


def test_replaces_single_pii():
    assert scrub_pii("Hello Max Mustermann", ["Max Mustermann"]) == "Hello [REDACTED]"


def test_replaces_multiple_pii():
    result = scrub_pii(
        "Name: Anna Schmidt, IBAN: DE89370400440532013000",
        ["Anna Schmidt", "DE89370400440532013000"],
    )
    assert result == "Name: [REDACTED], IBAN: [REDACTED]"


def test_case_insensitive():
    assert scrub_pii("Hello max mustermann", ["Max Mustermann"]) == "Hello [REDACTED]"


def test_empty_pii_list():
    assert scrub_pii("Hello world", []) == "Hello world"


def test_multiple_occurrences():
    assert scrub_pii("Max called. Max left.", ["Max"]) == "[REDACTED] called. [REDACTED] left."
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend\nuv run pytest tests/test_scrubber.py -v
```

Expected: ERROR — `ModuleNotFoundError: No module named 'services.scrubber'`

- [ ] **Step 3: Implement scrubber**

```python
# backend/services/scrubber.py
import re


def scrub_pii(text: str, pii_list: list[str]) -> str:
    result = text
    for pii in pii_list:
        escaped = re.escape(pii)
        result = re.sub(escaped, "[REDACTED]", result, flags=re.IGNORECASE)
    return result
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend\nuv run pytest tests/test_scrubber.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add backend/services/scrubber.py backend/tests/test_scrubber.py
git commit -m "feat: add PII scrubber with tests"
```

---

## Task 4: Implement Ollama/Gemma 4 Service

**Files:**
- Create: `backend/services/ollama.py`
- Create: `backend/tests/test_ollama.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_ollama.py
import pytest
from unittest.mock import AsyncMock, patch
from services.ollama import call_gemma4


@pytest.mark.asyncio
async def test_returns_parsed_result():
    mock_response = {
        "raw_text": "Rechnung Nr. 123",
        "pii_list": ["Max Mustermann"],
    }
    mock_resp = AsyncMock()
    mock_resp.raise_for_status = AsyncMock()
    mock_resp.json = AsyncMock(return_value={"response": '{"raw_text": "Rechnung Nr. 123", "pii_list": ["Max Mustermann"]}'})

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        result = await call_gemma4("base64data")

    assert result.raw_text == "Rechnung Nr. 123"
    assert result.pii_list == ["Max Mustermann"]


@pytest.mark.asyncio
async def test_raises_on_http_error():
    import httpx
    with patch("httpx.AsyncClient.post", side_effect=httpx.HTTPStatusError("500", request=None, response=None)):
        with pytest.raises(httpx.HTTPStatusError):
            await call_gemma4("base64data")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend\nuv run pytest tests/test_ollama.py -v
```

Expected: ERROR — `ModuleNotFoundError: No module named 'services.ollama'`

- [ ] **Step 3: Implement Ollama service**

```python
# backend/services/ollama.py
import json
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend\nuv run pytest tests/test_ollama.py -v
```

Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add backend/services/ollama.py backend/tests/test_ollama.py
git commit -m "feat: add Ollama/Gemma4 OCR+PII service with structured output"
```

---

## Task 5: Implement OpenAI Service

**Files:**
- Create: `backend/services/openai_service.py`
- Create: `backend/tests/test_openai_service.py`

- [ ] **Step 1: Write failing test**

```python
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
        mock_client.beta.chat.completions.parse = MagicMock(return_value=mock_parsed)
        result = await call_openai("Strom Rechnung text here")

    assert result.document_type == "invoice"
    assert result.translation == "Dear customer, your bill is due."
    assert len(result.actions) == 1
    assert result.actions[0].deadline == "2026-04-30"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend\nuv run pytest tests/test_openai_service.py -v
```

Expected: ERROR — `ModuleNotFoundError: No module named 'services.openai_service'`

- [ ] **Step 3: Implement OpenAI service**

```python
# backend/services/openai_service.py
import os
from openai import OpenAI
from models import TranslationResult

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend\nuv run pytest tests/test_openai_service.py -v
```

Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add backend/services/openai_service.py backend/tests/test_openai_service.py
git commit -m "feat: add OpenAI translation service with structured output"
```

---

## Task 6: Implement Vault Writer

**Files:**
- Create: `backend/services/vault.py`

- [ ] **Step 1: Implement vault writer**

```python
# backend/services/vault.py
from datetime import date
from pathlib import Path
from models import TranslationResult

VAULT_DIR = Path.home() / "Documents" / "paperwork-vault"


def write_to_vault(result: TranslationResult) -> str:
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    filename = f"{today}-{result.document_type}.md"
    path = VAULT_DIR / filename

    action_lines = "\n".join(
        f"- [ ] {a.description}" + (f" (by {a.deadline})" if a.deadline else "")
        for a in result.actions
    )

    content = f"""---
date: {today}
type: {result.document_type}
---

## Summary
{result.summary}

## Translation
{result.translation}

## Actions
{action_lines}
"""
    path.write_text(content, encoding="utf-8")
    return str(path)
```

- [ ] **Step 2: Commit**

```bash
git add backend/services/vault.py
git commit -m "feat: add Obsidian-compatible markdown vault writer"
```

---

## Task 7: Wire Up FastAPI Endpoint with Langfuse

**Files:**
- Modify: `backend/main.py`

- [ ] **Step 1: Add /process endpoint with Langfuse tracing**

Replace `backend/main.py` with:

```python
# backend/main.py
from dotenv import load_dotenv
load_dotenv()

import base64
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from langfuse import Langfuse
from langfuse.openai import openai as langfuse_openai  # patches openai automatically

from services.ollama import call_gemma4
from services.scrubber import scrub_pii
from services.openai_service import call_openai
from services.vault import write_to_vault
from models import TranslationResult

app = FastAPI(title="Paperwork Assistant")
langfuse = Langfuse()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/process", response_model=TranslationResult)
async def process_document(file: UploadFile = File(...)):
    image_bytes = await file.read()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    trace = langfuse.trace(name="process-document")

    # Step 1: OCR + PII detection via Gemma 4
    ocr_span = trace.generation(
        name="gemma4-ocr-pii",
        model="gemma3:4b",
        input={"prompt": "OCR + PII detection", "image": "[base64 image]"},
    )
    ocr_result = await call_gemma4(image_base64)
    ocr_span.end(output=ocr_result.model_dump())

    # Step 2: Scrub PII on server
    clean_text = scrub_pii(ocr_result.raw_text, ocr_result.pii_list)

    # Step 3: Translate + extract actions via OpenAI
    # (Langfuse OpenAI wrapper auto-traces this call)
    translation_span = trace.generation(
        name="openai-translate-actions",
        model="gpt-4o",
        input={"text": clean_text},
    )
    translation_result = await call_openai(clean_text)
    translation_span.end(output=translation_result.model_dump())

    # Step 4: Write to vault
    write_to_vault(translation_result)

    langfuse.flush()
    return translation_result
```

- [ ] **Step 2: Verify endpoint works locally**

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Test with a sample image:
```bash
curl -X POST http://localhost:8000/process \
  -F "file=@/path/to/sample-german-doc.jpg"
```

Expected: JSON response with `document_type`, `translation`, `summary`, `actions`

Check `~/Documents/paperwork-vault/` for the markdown file.
Check Langfuse dashboard for a new trace with two generations.

- [ ] **Step 3: Commit**

```bash
git add backend/main.py
git commit -m "feat: add /process endpoint with full pipeline and Langfuse tracing"
```

---

## Task 8: Bootstrap Expo Mobile App

**Files:**
- Create: `mobile/` (Expo project)
- Create: `mobile/src/types.ts`
- Create: `mobile/.env.example`

- [ ] **Step 1: Create Expo app**

```bash
cd langfuse-hackathon
npx create-expo-app@latest mobile --template blank-typescript
```

- [ ] **Step 2: Install dependencies**

```bash
cd mobile
npx expo install expo-image-picker
```

- [ ] **Step 3: Create .env.example**

```bash
cat > .env.example << 'EOF'
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.X:8000
EOF
cp .env.example .env
```

Set `EXPO_PUBLIC_API_BASE_URL` to your laptop's local IP:
```bash
ipconfig getifaddr en0   # macOS — find your WiFi IP
```

- [ ] **Step 4: Create shared types**

```typescript
// mobile/src/types.ts
export interface Action {
  description: string;
  deadline: string | null;
}

export interface TranslationResult {
  document_type: string;
  translation: string;
  summary: string;
  actions: Action[];
}
```

- [ ] **Step 5: Commit**

```bash
git add mobile/
git commit -m "feat: bootstrap Expo mobile app"
```

---

## Task 9: Build Mobile App Screens

**Files:**
- Create: `mobile/app/_layout.tsx`
- Create: `mobile/app/index.tsx`
- Create: `mobile/app/result.tsx`

- [ ] **Step 1: Create root layout**

```typescript
// mobile/app/_layout.tsx
import { Stack } from 'expo-router';

export default function RootLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: 'Paperwork Assistant' }} />
      <Stack.Screen name="result" options={{ title: 'Document Result' }} />
    </Stack>
  );
}
```

- [ ] **Step 2: Create home screen**

```typescript
// mobile/app/index.tsx
import { useState } from 'react';
import {
  View, Text, TouchableOpacity, ActivityIndicator,
  StyleSheet, Alert
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { useRouter } from 'expo-router';
import { TranslationResult } from '../src/types';

const API_BASE = process.env.EXPO_PUBLIC_API_BASE_URL;

export default function HomeScreen() {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function pickAndProcess() {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert('Permission required', 'Please allow photo library access.');
      return;
    }

    const picked = await ImagePicker.launchImageLibraryAsync({ quality: 0.8 });
    if (picked.canceled) return;

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', {
        uri: picked.assets[0].uri,
        name: 'document.jpg',
        type: 'image/jpeg',
      } as any);

      const response = await fetch(`${API_BASE}/process`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error(`Server error: ${response.status}`);

      const result: TranslationResult = await response.json();
      router.push({ pathname: '/result', params: { result: JSON.stringify(result) } });
    } catch (err: any) {
      Alert.alert('Error', err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>German Paperwork Assistant</Text>
      <Text style={styles.subtitle}>Upload a German document to translate and get action items</Text>
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#3B82F6" />
          <Text style={styles.status}>Processing document...</Text>
        </View>
      ) : (
        <TouchableOpacity style={styles.button} onPress={pickAndProcess}>
          <Text style={styles.buttonText}>Upload Document</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24, backgroundColor: '#F9FAFB' },
  title: { fontSize: 24, fontWeight: 'bold', marginBottom: 8, textAlign: 'center' },
  subtitle: { fontSize: 14, color: '#6B7280', textAlign: 'center', marginBottom: 40 },
  button: { backgroundColor: '#3B82F6', paddingHorizontal: 32, paddingVertical: 16, borderRadius: 12 },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  loadingContainer: { alignItems: 'center', gap: 16 },
  status: { fontSize: 14, color: '#6B7280' },
});
```

- [ ] **Step 3: Create result screen**

```typescript
// mobile/app/result.tsx
import { useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet
} from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { TranslationResult } from '../src/types';

export default function ResultScreen() {
  const { result } = useLocalSearchParams<{ result: string }>();
  const doc: TranslationResult = JSON.parse(result);
  const [translationExpanded, setTranslationExpanded] = useState(false);
  const [checked, setChecked] = useState<boolean[]>(doc.actions.map(() => false));

  return (
    <ScrollView style={styles.scroll} contentContainerStyle={styles.container}>
      <View style={styles.badge}>
        <Text style={styles.badgeText}>{doc.document_type.toUpperCase()}</Text>
      </View>

      <Text style={styles.label}>Summary</Text>
      <Text style={styles.body}>{doc.summary}</Text>

      <TouchableOpacity
        style={styles.row}
        onPress={() => setTranslationExpanded(v => !v)}
      >
        <Text style={styles.label}>Full Translation</Text>
        <Text style={styles.chevron}>{translationExpanded ? '▲' : '▼'}</Text>
      </TouchableOpacity>
      {translationExpanded && (
        <Text style={styles.translation}>{doc.translation}</Text>
      )}

      <Text style={styles.label}>Actions Required</Text>
      {doc.actions.map((action, i) => (
        <TouchableOpacity
          key={i}
          style={styles.actionRow}
          onPress={() => setChecked(prev => prev.map((v, j) => j === i ? !v : v))}
        >
          <Text style={styles.checkbox}>{checked[i] ? '☑' : '☐'}</Text>
          <View style={{ flex: 1 }}>
            <Text style={[styles.actionText, checked[i] && styles.done]}>
              {action.description}
            </Text>
            {action.deadline && (
              <Text style={styles.deadline}>Due: {action.deadline}</Text>
            )}
          </View>
        </TouchableOpacity>
      ))}

      <View style={styles.savedBanner}>
        <Text style={styles.savedText}>Saved to vault on your laptop</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: { flex: 1, backgroundColor: '#F9FAFB' },
  container: { padding: 24, gap: 12 },
  badge: { backgroundColor: '#DBEAFE', paddingHorizontal: 12, paddingVertical: 4, borderRadius: 8, alignSelf: 'flex-start' },
  badgeText: { color: '#1D4ED8', fontWeight: '700', fontSize: 12 },
  label: { fontSize: 16, fontWeight: '700', color: '#111827', marginTop: 8 },
  body: { fontSize: 14, color: '#374151', lineHeight: 22 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  chevron: { fontSize: 14, color: '#6B7280' },
  translation: { fontSize: 13, color: '#6B7280', lineHeight: 20, fontStyle: 'italic' },
  actionRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 10, paddingVertical: 6 },
  checkbox: { fontSize: 20, color: '#3B82F6' },
  actionText: { fontSize: 14, color: '#374151' },
  done: { textDecorationLine: 'line-through', color: '#9CA3AF' },
  deadline: { fontSize: 12, color: '#EF4444', marginTop: 2 },
  savedBanner: { backgroundColor: '#D1FAE5', borderRadius: 8, padding: 12, marginTop: 16 },
  savedText: { color: '#065F46', fontWeight: '600' },
});
```

- [ ] **Step 4: Commit**

```bash
git add mobile/app/
git commit -m "feat: add home and result screens"
```

---

## Task 10: Run Tests & End-to-End Verification

- [ ] **Step 1: Run full backend test suite**

```bash
cd backend\nuv run pytest -v
```

Expected:
```
PASSED tests/test_scrubber.py::test_replaces_single_pii
PASSED tests/test_scrubber.py::test_replaces_multiple_pii
PASSED tests/test_scrubber.py::test_case_insensitive
PASSED tests/test_scrubber.py::test_empty_pii_list
PASSED tests/test_scrubber.py::test_multiple_occurrences
PASSED tests/test_ollama.py::test_returns_parsed_result
PASSED tests/test_ollama.py::test_raises_on_http_error
PASSED tests/test_openai_service.py::test_returns_translation_result

8 passed
```

- [ ] **Step 2: Start Ollama**

```bash
OLLAMA_HOST=0.0.0.0 ollama serve
# new terminal:
ollama pull gemma3:4b
```

- [ ] **Step 3: Start FastAPI backend**

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- [ ] **Step 4: Start Expo app**

```bash
cd mobile
npx expo start
```

Open on physical device (same WiFi as laptop). Pick a German document image. Verify:
- Loading spinner shows
- Result screen shows document type, summary, collapsible translation, action checklist
- "Saved to vault" banner appears
- `~/Documents/paperwork-vault/` contains a new `.md` file
- Langfuse dashboard shows one trace with two generations (`gemma4-ocr-pii`, `openai-translate-actions`)

- [ ] **Step 5: Final commit**

```bash
git add .
git commit -m "feat: complete German paperwork assistant prototype"
```

---

## Environment Checklist

Before running end-to-end:
- [ ] `backend/.env` filled with real `OPENAI_API_KEY`, `LANGFUSE_*` keys
- [ ] `mobile/.env` has correct `EXPO_PUBLIC_API_BASE_URL` (laptop's WiFi IP)
- [ ] Ollama running: `OLLAMA_HOST=0.0.0.0 ollama serve`
- [ ] Gemma model pulled: `ollama pull gemma3:4b`
- [ ] Phone and laptop on same WiFi network
