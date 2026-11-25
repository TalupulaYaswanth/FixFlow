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
from typing import List, Optional, Dict, Any, Tuple
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


def trim_common_affixes(orig: str, rep: str) -> Tuple[str, str]:
    """Trims matching non-alphanumeric punctuation from boundaries."""
    while orig and rep and orig[0] == rep[0] and not orig[0].isalnum():
        orig = orig[1:]
        rep = rep[1:]
    while orig and rep and orig[-1] == rep[-1] and not orig[-1].isalnum():
        orig = orig[:-1]
        rep = rep[:-1]
    return orig.strip(), rep.strip()


def reconcile_changes_with_diff(
    original_text: str,
    corrected_text: str,
    raw_changes: List[Dict[str, Any]],
    diff_chunks: List[Any]
) -> List[Dict[str, Any]]:
    """
    Reconciles raw multi-tier pipeline changes with ground-truth LCS diff chunks.
    Guarantees:
      - 1-to-1 match with the Visual Diff
      - 'original' is guaranteed to exist in the user's input text
      - 'replacement' is guaranteed to exist in the final corrected text
      - Intermediate ghost changes (e.g. lazi -> nazi -> lazy) are collapsed into lazi -> lazy
      - Rich linguistic rules and explanations from Gemini AI and heuristics are preserved
    """
    def get_chunk_info(c):
        if isinstance(c, (list, tuple)):
            return c[0], c[1]
        elif isinstance(c, dict):
            return c.get('type'), c.get('text', '')
        return getattr(c, 'type', None), getattr(c, 'text', '')

    edits = []
    i = 0
    n = len(diff_chunks)

    while i < n:
        c_type, c_text = get_chunk_info(diff_chunks[i])
        if c_type == 'equal':
            i += 1
            continue

        del_parts = []
        ins_parts = []

        while i < n:
            cur_type, cur_text = get_chunk_info(diff_chunks[i])
            if cur_type == 'equal':
                break
            elif cur_type == 'delete':
                del_parts.append(cur_text)
            elif cur_type == 'insert':
                ins_parts.append(cur_text)
            i += 1

        raw_orig = "".join(del_parts).strip()
        raw_rep = "".join(ins_parts).strip()
        orig_str, rep_str = trim_common_affixes(raw_orig, raw_rep)

        if not orig_str and not rep_str:
            continue
        if orig_str == rep_str:
            continue

        edits.append({"original": orig_str, "replacement": rep_str})

    reconciled = []
    used_raw = set()

    for edit in edits:
        orig = edit["original"]
        rep = edit["replacement"]

        matched_rule = None
        matched_expl = None
        matched_idx = -1

        # 1. Exact match on both original and replacement
        for idx, c in enumerate(raw_changes):
            if idx in used_raw:
                continue
            c_orig = str(c.get("original", "")).strip()
            c_rep = str(c.get("replacement", "")).strip()
            if c_orig.lower() == orig.lower() and c_rep.lower() == rep.lower():
                matched_rule = c.get("rule") or c.get("type")
                matched_expl = c.get("explanation")
                matched_idx = idx
                break

        # 2. Intermediate chain collapse (orig -> X, X -> rep)
        if not matched_rule:
            for idx1, c1 in enumerate(raw_changes):
                c1_orig = str(c1.get("original", "")).strip()
                c1_rep = str(c1.get("replacement", "")).strip()
                if c1_orig.lower() == orig.lower():
                    for idx2, c2 in enumerate(raw_changes):
                        c2_orig = str(c2.get("original", "")).strip()
                        c2_rep = str(c2.get("replacement", "")).strip()
                        if c2_orig.lower() == c1_rep.lower() and c2_rep.lower() == rep.lower():
                            matched_rule = c2.get("rule") or c1.get("rule") or c2.get("type") or c1.get("type")
                            matched_expl = c2.get("explanation") or c1.get("explanation")
                            used_raw.add(idx1)
                            used_raw.add(idx2)
                            break
                    if matched_rule:
                        break

        # 3. Substring / Token overlap match
        if not matched_rule:
            for idx, c in enumerate(raw_changes):
                if idx in used_raw:
                    continue
                c_orig = str(c.get("original", "")).strip()
                c_rep = str(c.get("replacement", "")).strip()
                if c_orig and c_rep:
                    if (c_orig.lower() in orig.lower() or orig.lower() in c_orig.lower()) and \
                       (c_rep.lower() in rep.lower() or rep.lower() in c_rep.lower()):
                        matched_rule = c.get("rule") or c.get("type")
                        matched_expl = c.get("explanation")
                        matched_idx = idx
                        break

        if matched_idx != -1:
            used_raw.add(matched_idx)

        # 4. Fallback inference based on linguistics
        if not matched_rule:
            if not orig and rep:
                matched_rule = "Syntactic Insertion"
                matched_expl = f"Inserted '{rep}' for complete grammatical structure."
            elif orig and not rep:
                matched_rule = "Redundancy Elimination"
                matched_expl = f"Removed duplicate or unnecessary word '{orig}'."
            elif orig.lower() == rep.lower():
                matched_rule = "Capitalization & Typography"
                matched_expl = f"Adjusted case/formatting for '{orig}'."
            elif levenshtein_distance(orig, rep) <= 2:
                matched_rule = "Spelling (DP Levenshtein)"
                matched_expl = f"Corrected typo '{orig}' to '{rep}'."
            else:
                matched_rule = "Contextual Linguistic Polish"
                matched_expl = f"Refined '{orig}' to '{rep}' for sentence context and flow."

        reconciled.append({
            "original": orig,
            "replacement": rep,
            "rule": matched_rule,
            "explanation": matched_expl or f"Transformed '{orig}' to '{rep}'."
        })

    return reconciled


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
        # Step 1: Base space-optimized DP Levenshtein pass (fixes non-word spelling errors)
        dp_text, dp_changes = dp_engine.correct_text(input_text)
        corrected_text = dp_text
        changes = list(dp_changes)

        # Step 2: Context-aware pass (resolves real-word homophones, collocations, context errors)
        if should_use_llm and nlp_engine.genai_client:
            ai_res = nlp_engine.correct_context_aware_with_llm(corrected_text, mode="spell")
            if ai_res is not None:
                ai_text, ai_changes = ai_res
                if ai_text and ai_text.strip() != corrected_text.strip():
                    corrected_text = ai_text
                    changes.extend(ai_changes)
        else:
            ctx_text, ctx_changes = nlp_engine.correct_context_heuristics(corrected_text)
            if ctx_text != corrected_text:
                corrected_text = ctx_text
                changes.extend(ctx_changes)

    elif payload.mode == CorrectionMode.GRAMMAR:
        # Step 1: Multi-tier local model pass (DP spelling -> NLP grammar)
        spell_text, spell_changes = dp_engine.correct_text(input_text)
        grammar_text, grammar_changes = nlp_engine.fix_grammar(spell_text)
        corrected_text = grammar_text
        changes = spell_changes + grammar_changes

        # Step 2: Context-aware AI refinement pass using Gemini API
        if should_use_llm and nlp_engine.genai_client:
            ai_res = nlp_engine.correct_context_aware_with_llm(corrected_text, mode="grammar")
            if ai_res is not None:
                ai_text, ai_changes = ai_res
                if ai_text and ai_text.strip() != corrected_text.strip():
                    corrected_text = ai_text
                    changes.extend(ai_changes)

    elif payload.mode == CorrectionMode.TONE:
        target_tone = payload.tone.value if payload.tone else "formal"
        # Step 1: Multi-tier local model pass (DP spelling -> Tone polish)
        spell_text, spell_changes = dp_engine.correct_text(input_text)
        tone_text, tone_changes = nlp_engine.polish_tone(spell_text, target_tone=target_tone)
        corrected_text = tone_text
        changes = spell_changes + tone_changes

        # Step 2: Context-aware AI refinement pass using Gemini API
        if should_use_llm and nlp_engine.genai_client:
            ai_res = nlp_engine.correct_context_aware_with_llm(corrected_text, mode="tone", tone=target_tone)
            if ai_res is not None:
                ai_text, ai_changes = ai_res
                if ai_text and ai_text.strip() != corrected_text.strip():
                    corrected_text = ai_text
                    changes.extend(ai_changes)

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported mode: {payload.mode}")

    raw_diff = lcs_diff(input_text, corrected_text, mode="word")
    diff_chunks = [DiffChunk(type=op, text=val) for op, val in raw_diff]
    edit_dist = levenshtein_distance(input_text, corrected_text)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    # Reconcile raw multi-tier pipeline changes with ground-truth visual diff
    reconciled_changes = reconcile_changes_with_diff(input_text, corrected_text, changes, diff_chunks)

    return CorrectionResponse(
        original_text=input_text,
        corrected_text=corrected_text,
        mode=payload.mode.value,
        changes=reconciled_changes,
        diff=diff_chunks,
        metrics=Metrics(
            processing_time_ms=round(elapsed_ms, 2),
            original_char_count=len(input_text),
            corrected_char_count=len(corrected_text),
            original_word_count=len(input_text.split()),
            corrected_word_count=len(corrected_text.split()),
            total_edits=len(reconciled_changes),
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


class DocumentStructureRequest(BaseModel):
    text: str = Field(..., description="Raw extracted document text to structure")
    filename: Optional[str] = Field(None, description="Original document filename")


@app.post("/upload-file", tags=["File Processing"])
async def upload_file_endpoint(
    file: UploadFile = File(...),
    mode: str = Form("spell"),
    tone: str = Form("formal"),
    ai_structure: bool = Form(True)
):
    """
    Upload a file (.pptx, .docx, .pdf, .txt), extract its text, and return
    both the extracted content (optionally AI-structured via Gemini) and the FixFlow-corrected version.
    """
    file_bytes = await file.read()
    try:
        extracted_text, file_type, metadata = parse_uploaded_file(file.filename, file_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File parse error: {str(e)}")

    # Apply AI document structuring if enabled
    raw_extracted = extracted_text
    if ai_structure and extracted_text and not extracted_text.startswith("["):
        try:
            structured_text, s_changes = nlp_engine.structure_document(extracted_text, filename=file.filename)
            if structured_text and structured_text.strip():
                extracted_text = structured_text
                metadata["ai_structured"] = True
        except Exception:
            pass

    # Run multi-tier pipeline correction
    # Note: To ensure upload responses are instantaneous (<1s) even for large multi-page PDFs,
    # we correct an executive preview sample, leaving full document correction for studio action buttons.
    corrected = extracted_text
    changes = []
    if mode != "none" and extracted_text and not extracted_text.startswith("["):
        sample_to_correct = extracted_text[:2500]
        if mode == "spell":
            c_sample, changes = dp_engine.correct_text(sample_to_correct)
            corrected = c_sample + extracted_text[2500:]
        elif mode == "grammar":
            s_text, s_changes = dp_engine.correct_text(sample_to_correct)
            c_sample, g_changes = nlp_engine.fix_grammar(s_text)
            changes = s_changes + g_changes
            corrected = c_sample + extracted_text[2500:]
        elif mode == "presentation" and file_type == "pptx":
            corrected, changes = prompt_opt.optimize_presentation_slides(extracted_text)
        else:
            s_text, s_changes = dp_engine.correct_text(sample_to_correct)
            c_sample, t_changes = nlp_engine.polish_tone(s_text, target_tone=tone)
            changes = s_changes + t_changes
            corrected = c_sample + extracted_text[2500:]

    raw_diff = lcs_diff(extracted_text[:2000], corrected[:2000], mode="word")
    edit_dist = levenshtein_distance(extracted_text[:800], corrected[:800])
    reconciled_changes = reconcile_changes_with_diff(extracted_text[:2000], corrected[:2000], changes, raw_diff)

    return {
        "filename": file.filename,
        "file_type": file_type,
        "metadata": metadata,
        "raw_extracted_text": raw_extracted,
        "extracted_text": extracted_text,
        "corrected_text": corrected,
        "diff_preview": [{"type": op, "text": val} for op, val in raw_diff],
        "total_edits": len(reconciled_changes),
        "changes": reconciled_changes,
        "sample_edit_distance": edit_dist
    }


@app.post("/structure-document", tags=["File Processing"])
async def structure_document_endpoint(payload: DocumentStructureRequest):
    """
    Transforms raw document text into clean, hierarchical Markdown with headings,
    parallel bullets, and tables using Google Gemini AI API.
    """
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="Empty text provided.")

    structured_text, changes = nlp_engine.structure_document(payload.text, filename=payload.filename)
    return {
        "original_text": payload.text,
        "structured_text": structured_text,
        "changes": changes,
        "ai_powered": nlp_engine.genai_client is not None
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

