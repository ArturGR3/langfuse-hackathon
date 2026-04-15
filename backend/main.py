from dotenv import load_dotenv
load_dotenv()

import base64
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from langfuse import observe, get_client

from services.ollama import call_gemma4
from services.scrubber import scrub_pii
from services.openai_service import call_openai
from services.vault import write_to_vault
from models import TranslationResult

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


@app.post("/process", response_model=TranslationResult)
async def process_document(file: UploadFile = File(...)):
    image_bytes = await file.read()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    # Step 1: OCR + PII detection via Gemma 4
    ocr_result = await call_gemma4(image_base64)

    # Step 2: Scrub PII
    clean_text = scrub_pii(ocr_result.raw_text, ocr_result.pii_list)

    # Step 3: Translate + extract actions via OpenAI
    translation_result = await call_openai(clean_text)

    # Step 4: Write to vault
    write_to_vault(translation_result)

    get_client().flush()
    return translation_result
