"""
FixFlow: Smart Text Correction Powered by Dynamic Programming & NLP
Module: main.py

FastAPI Backend Server providing RESTful endpoints for:
- /correct: Multi-mode text correction (Spell Check via DP, Grammar Fix via NLP, Tone Polishing)
- /suggestions: Top-K candidate generation using space-optimized Levenshtein distance
- /diff: LCS-based side-by-side diff generator
- /optimize-prompt: Domain-specific prompt optimization (AI Prompt, Email, Presentation, etc.)
- /upload-file: File upload & extraction endpoint (.pptx, .docx, .pdf, .txt)
- /health: System health and diagnostic info
"""

import time
import os
from typing import List, Optional, Dict, Any
from enum import Enum

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from dp_corrector import DPCorrector, levenshtein_distance, lcs_diff
from nlp_corrector import NLPCorrector
from document_parser import parse_uploaded_file
from prompt_optimizer import PromptOptimizer


# ---------------------------------------------------------------------------
# App Initialization & Middleware
# ---------------------------------------------------------------------------
app = FastAPI(
    title="FixFlow API",
    description="Smart Text Correction Engine Powered by Dynamic Programming & NLP",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate core engines
dp_engine = DPCorrector()
nlp_engine = NLPCorrector()
prompt_opt = PromptOptimizer(dp_engine, nlp_engine)


# ---------------------------------------------------------------------------
# Data Models (Pydantic)
# ---------------------------------------------------------------------------

class CorrectionMode(str, Enum):
    SPELL = "spell"
    GRAMMAR = "grammar"
    TONE = "tone"


class ToneStyle(str, Enum):
    FORMAL = "formal"
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    CONCISE = "concise"


class PromptType(str, Enum):
    GENERAL = "general"
    AI_PROMPT = "ai_prompt"
    EMAIL = "email"
    PRESENTATION = "presentation"


class CorrectionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000, description="The input text to correct")
    mode: CorrectionMode = Field(default=CorrectionMode.SPELL, description="Correction mode ('spell', 'grammar', 'tone')")
    tone: Optional[ToneStyle] = Field(default=ToneStyle.FORMAL, description="Target tone style if mode is 'tone'")
    use_llm: Optional[bool] = Field(default=None, description="Attempt LLM GenAI enhancement if available")


class DiffChunk(BaseModel):
    type: str  # 'equal', 'delete', 'insert'
    text: str


class Metrics(BaseModel):
    processing_time_ms: float
    original_char_count: int
    corrected_char_count: int
    original_word_count: int
    corrected_word_count: int
    total_edits: int
    levenshtein_distance: int


class CorrectionResponse(BaseModel):
    original_text: str
    corrected_text: str
    mode: str
    changes: List[Dict[str, Any]]
    diff: List[DiffChunk]
    metrics: Metrics


class SuggestionRequest(BaseModel):
    word: str = Field(..., min_length=1, max_length=50, description="Word to find spelling suggestions for")
    k: int = Field(default=3, ge=1, le=10, description="Number of suggestions to return")
    max_distance: int = Field(default=3, ge=1, le=5, description="Maximum edit distance threshold")


class SuggestionItem(BaseModel):
    word: str
    edit_distance: int
    confidence_score: float


class SuggestionResponse(BaseModel):
    query_word: str
    suggestions: List[SuggestionItem]
    computation_time_ms: float


class DiffRequest(BaseModel):
    original_text: str
    modified_text: str
    granularity: str = Field(default="word", description="'word' or 'char'")


class EmailOptimizeRequest(BaseModel):
    subject: str = Field(default="", description="Email subject line")
    body: str = Field(..., min_length=1, description="Email body content")
    salutation: Optional[str] = Field(default="Hi Team,", description="Email greeting")
    signoff: Optional[str] = Field(default="Best regards,", description="Email sign-off")
    tone: Optional[ToneStyle] = Field(default=ToneStyle.PROFESSIONAL, description="Desired email tone")


class AIPromptOptimizeRequest(BaseModel):
    raw_prompt: str = Field(..., min_length=1, description="Raw input prompt to structure & optimize")
    target_model: Optional[str] = Field(default="Universal LLM", description="Target model (Gemini, Claude, GPT)")


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint indicating API availability and model status."""
    return {
        "status": "healthy",
        "service": "FixFlow Core API",
        "version": "2.0.0",
        "dp_engine": "active",
        "vocabulary_size": len(dp_engine.vocab),
        "nlp_engine": "active",
        "supported_file_types": [".pptx", ".docx", ".pdf", ".txt", ".md"],
        "supported_prompt_types": ["ai_prompt", "email", "presentation", "general"],
        "llm_available": nlp_engine.genai_client is not None
    }


@app.post("/correct", response_model=CorrectionResponse, tags=["Correction"])
def correct_text(payload: CorrectionRequest):
    """
    Primary FixFlow correction endpoint.
    """
    start_time = time.perf_counter()
    input_text = payload.text
    changes = []
    corrected_text = input_text

    should_use_llm = payload.use_llm if payload.use_llm is not None else (nlp_engine.genai_client is not None)

    if payload.mode == CorrectionMode.SPELL:
        corrected_text, changes = dp_engine.correct_text(input_text)

    elif payload.mode == CorrectionMode.GRAMMAR:
        llm_result = None
        if should_use_llm:
            llm_result = nlp_engine.correct_with_llm(input_text, mode="grammar")

        if llm_result is not None:
            corrected_text, changes = llm_result
        else:
            # Multi-tier pipeline: DP spelling pass -> NLP grammar pass
            spell_text, spell_changes = dp_engine.correct_text(input_text)
            grammar_text, grammar_changes = nlp_engine.fix_grammar(spell_text)
            corrected_text = grammar_text
            changes = spell_changes + grammar_changes

    elif payload.mode == CorrectionMode.TONE:
        target_tone = payload.tone.value if payload.tone else "formal"
        llm_result = None
        if should_use_llm:
            llm_result = nlp_engine.correct_with_llm(input_text, mode="tone", tone=target_tone)

        if llm_result is not None:
            corrected_text, changes = llm_result
        else:
            # Multi-tier pipeline: DP spelling pass -> Tone polish pass (with grammar cleanup)
            spell_text, spell_changes = dp_engine.correct_text(input_text)
            tone_text, tone_changes = nlp_engine.polish_tone(spell_text, target_tone=target_tone)
            corrected_text = tone_text
            changes = spell_changes + tone_changes

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported mode: {payload.mode}")

    raw_diff = lcs_diff(input_text, corrected_text, mode="word")
    diff_chunks = [DiffChunk(type=op, text=val) for op, val in raw_diff]
    edit_dist = levenshtein_distance(input_text, corrected_text)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return CorrectionResponse(
        original_text=input_text,
        corrected_text=corrected_text,
        mode=payload.mode.value,
        changes=changes,
        diff=diff_chunks,
        metrics=Metrics(
            processing_time_ms=round(elapsed_ms, 2),
            original_char_count=len(input_text),
            corrected_char_count=len(corrected_text),
            original_word_count=len(input_text.split()),
            corrected_word_count=len(corrected_text.split()),
            total_edits=len(changes),
            levenshtein_distance=edit_dist
        )
    )


@app.post("/suggestions", response_model=SuggestionResponse, tags=["Spell Check"])
def get_suggestions(payload: SuggestionRequest):
    """Generates top-K spelling suggestions using space-optimized Levenshtein distance."""
    start_time = time.perf_counter()
    raw_suggs = dp_engine.get_suggestions(
        word=payload.word,
        k=payload.k,
        max_distance=payload.max_distance
    )
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    items = [
        SuggestionItem(word=w, edit_distance=dist, confidence_score=conf)
        for w, dist, conf in raw_suggs
    ]

    return SuggestionResponse(
        query_word=payload.word,
        suggestions=items,
        computation_time_ms=round(elapsed_ms, 2)
    )


@app.post("/diff", tags=["Algorithms"])
def compute_diff(payload: DiffRequest):
    """Direct endpoint for LCS Dynamic Programming Diff generation."""
    raw_diff = lcs_diff(payload.original_text, payload.modified_text, mode=payload.granularity)
    return {
        "original": payload.original_text,
        "modified": payload.modified_text,
        "granularity": payload.granularity,
        "diff_chunks": [{"type": op, "text": val} for op, val in raw_diff]
    }


@app.post("/optimize/email", tags=["Prompt Types"])
def optimize_email_endpoint(payload: EmailOptimizeRequest):
    """Specialized endpoint for email subject and body polishing."""
    email_dict, changes = prompt_opt.optimize_email(
        subject=payload.subject,
        body=payload.body,
        salutation=payload.salutation or "Hi Team,",
        signoff=payload.signoff or "Best regards,",
        email_tone=payload.tone.value if payload.tone else "professional"
    )
    return {
        "optimized_email": email_dict,
        "changes": changes,
        "total_changes": len(changes)
    }


@app.post("/optimize/ai-prompt", tags=["Prompt Types"])
def optimize_ai_prompt_endpoint(payload: AIPromptOptimizeRequest):
    """Structures and optimizes raw user prompts for AI models."""
    structured, changes = prompt_opt.optimize_ai_prompt(
        raw_prompt=payload.raw_prompt,
        target_model=payload.target_model or "Universal LLM"
    )
    return {
        "original_prompt": payload.raw_prompt,
        "optimized_prompt": structured,
        "changes": changes
    }


@app.post("/upload-file", tags=["File Processing"])
async def upload_file_endpoint(
    file: UploadFile = File(...),
    mode: str = Form("spell"),
    tone: str = Form("formal")
):
    """
    Upload a file (.pptx, .docx, .pdf, .txt), extract its text, and return
    both the extracted content and the FixFlow-corrected version.
    """
    file_bytes = await file.read()
    try:
        extracted_text, file_type, metadata = parse_uploaded_file(file.filename, file_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File parse error: {str(e)}")

    # Run multi-tier pipeline correction
    if mode == "spell":
        corrected, changes = dp_engine.correct_text(extracted_text)
    elif mode == "grammar":
        s_text, s_changes = dp_engine.correct_text(extracted_text)
        corrected, g_changes = nlp_engine.fix_grammar(s_text)
        changes = s_changes + g_changes
    elif mode == "presentation" and file_type == "pptx":
        corrected, changes = prompt_opt.optimize_presentation_slides(extracted_text)
    else:
        s_text, s_changes = dp_engine.correct_text(extracted_text)
        corrected, t_changes = nlp_engine.polish_tone(s_text, target_tone=tone)
        changes = s_changes + t_changes

    raw_diff = lcs_diff(extracted_text[:3000], corrected[:3000], mode="word")
    edit_dist = levenshtein_distance(extracted_text[:1000], corrected[:1000])

    return {
        "filename": file.filename,
        "file_type": file_type,
        "metadata": metadata,
        "extracted_text": extracted_text,
        "corrected_text": corrected,
        "diff_preview": [{"type": op, "text": val} for op, val in raw_diff],
        "total_edits": len(changes),
        "sample_edit_distance": edit_dist
    }


# ---------------------------------------------------------------------------
# Mount Frontend Static Files & SPA Root (FixFlow Web Studio)
# ---------------------------------------------------------------------------
frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")

@app.get("/", include_in_schema=False)
async def serve_index():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "FixFlow API is active. Explore documentation at /docs"}

if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

