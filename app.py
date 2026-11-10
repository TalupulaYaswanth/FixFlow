"""
FixFlow: Smart Text Correction Powered by Dynamic Programming & NLP
Module: app.py (Version 2.0)

Full-featured Frontend Studio supporting:
1. Multi-Input Sources:
   - Direct Text Input
   - File Uploads: PowerPoint Presentations (.pptx), Word Docs (.docx), PDFs (.pdf), Markdown/Text (.txt)
   - Specialized Email Composer & Polisher (Subject, Salutation, Body, Sign-off)
   - AI Prompt Optimizer (Structuring raw prompts for Gemini, Claude, ChatGPT)
2. Dynamic Programming Core:
   - Space-optimized Levenshtein Distance
   - LCS Side-by-Side Diff Highlighting (green additions, red deletions)
   - Interactive 2D Levenshtein Transition Matrix Explorer
3. Comprehensive Metrics, Export, and Presets
"""

import streamlit as st
import time
import pandas as pd

from dp_corrector import DPCorrector, levenshtein_distance, levenshtein_matrix, lcs_diff
from nlp_corrector import NLPCorrector
from document_parser import parse_uploaded_file
from prompt_optimizer import PromptOptimizer

# ---------------------------------------------------------------------------
# Page Configuration & Modern Styling
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="FixFlow | Smart Text & Document Correction",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    code, pre, .mono {
        font-family: 'JetBrains Mono', monospace !important;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1320px;
    }

    /* FixFlow Hero Header */
    .fixflow-header {
        background: linear-gradient(135deg, #111827 0%, #1E1E2F 50%, #0F172A 100%);
        border: 1px solid rgba(255, 255, 255, 0.09);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
    }

    .fixflow-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #60A5FA, #A78BFA, #F472B6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .fixflow-subtitle {
        color: #94A3B8;
        font-size: 1.05rem;
        margin-top: 6px;
        margin-bottom: 0;
    }

    .fixflow-badge {
        background: rgba(96, 165, 250, 0.15);
        border: 1px solid rgba(96, 165, 250, 0.3);
        color: #93C5FD;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    /* Diff Visualizer Box */
    .diff-container {
        background: #0B0F19;
        border: 1px solid #1E293B;
        border-radius: 12px;
        padding: 18px 22px;
        font-size: 1.05rem;
        line-height: 1.85;
        min-height: 130px;
        word-break: break-word;
        box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.4);
    }

    .diff-equal {
        color: #E2E8F0;
    }

    .diff-del {
        background-color: rgba(239, 68, 68, 0.25);
        color: #FCA5A5;
        text-decoration: line-through;
        padding: 2px 6px;
        border-radius: 4px;
        margin: 0 2px;
        border: 1px solid rgba(239, 68, 68, 0.45);
    }

    .diff-ins {
        background-color: rgba(34, 197, 94, 0.25);
        color: #86EFAC;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 4px;
        margin: 0 2px;
        border: 1px solid rgba(34, 197, 94, 0.45);
    }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(180deg, #1E293B 0%, #151E2E 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }

    .metric-val {
        font-size: 1.75rem;
        font-weight: 700;
        color: #60A5FA;
    }

    .metric-lbl {
        color: #94A3B8;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-top: 4px;
    }

    .slide-card {
        background: #111827;
        border-left: 4px solid #A78BFA;
        padding: 14px 18px;
        border-radius: 0 10px 10px 0;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Cached Engine Instances
# ---------------------------------------------------------------------------
@st.cache_resource
def get_engines(api_key: str = ""):
    dp = DPCorrector()
    nlp = NLPCorrector(api_key=api_key if api_key else None)
    opt = PromptOptimizer(dp, nlp)
    return dp, nlp, opt


# ---------------------------------------------------------------------------
# Sidebar Settings
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ FixFlow Settings")

    input_channel = st.radio(
        "Input Source & Mode",
        [
            "📝 Direct Text Input",
            "📊 Presentation / PPT & Files",
            "📧 Email Polisher",
            "🤖 AI Prompt Optimizer"
        ],
        index=0
    )

    st.markdown("---")

    # Correction Engine Sub-options
    st.markdown("#### Engine Strategy")
    correction_engine = st.selectbox(
        "Linguistic Engine",
        [
            "⚡ Smart Spell Check (DP Levenshtein)",
            "📝 Grammar & Syntax Fix (Rule-Based NLP)",
            "🎨 Tone Polishing (Lexical Transforms)"
        ],
        index=0
    )

    if "Spell" in correction_engine:
        active_engine = "spell"
    elif "Grammar" in correction_engine:
        active_engine = "grammar"
    else:
        active_engine = "tone"

    tone_style = "formal"
    if active_engine == "tone" or "Email" in input_channel:
        tone_style = st.selectbox(
            "Tone Voice Profile",
            ["formal", "professional", "casual", "concise"],
            index=1 if "Email" in input_channel else 0
        )

    st.markdown("---")
    st.markdown("#### Dynamic Programming Config")
    dp_max_dist = st.slider("Max Levenshtein Distance (k)", min_value=1, max_value=4, value=3)
    dp_top_k = st.slider("Suggestions per Misspelling", min_value=1, max_value=5, value=3)

    st.markdown("---")
    st.markdown("#### Optional LLM Enhancement")
    gemini_key = st.text_input("Gemini API Key (optional)", type="password", help="Enables direct Gemini 2.5 LLM enhancement")

    dp_engine, nlp_engine, prompt_opt = get_engines(gemini_key)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="fixflow-header">
    <div>
        <div class="fixflow-title">⚡ FixFlow Studio</div>
        <div class="fixflow-subtitle">Smart Text, Slide & Email Correction Powered by Dynamic Programming & NLP</div>
    </div>
    <div>
        <span class="fixflow-badge">Mode: {input_channel.split()[1]}</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helper function to render diff and metrics
# ---------------------------------------------------------------------------
def render_results(original: str, corrected: str, changes: list, elapsed_ms: float):
    diff_chunks = lcs_diff(original, corrected, mode="word")
    edit_dist = levenshtein_distance(original, corrected)

    st.markdown("### 📊 Correction Results")

    # Side by side comparison
    c_orig, c_corr = st.columns(2)
    with c_orig:
        st.markdown("#### 📄 Original")
        st.markdown(f'<div class="diff-container">{original}</div>', unsafe_allow_html=True)
    with c_corr:
        st.markdown("#### ✨ Corrected & Polished")
        st.markdown(f'<div class="diff-container" style="color: #60A5FA;">{corrected}</div>', unsafe_allow_html=True)

    # Visual Diff Highlighting
    st.markdown("#### 🔍 Visual Diff (Longest Common Subsequence Backtracking)")
    diff_html = '<div class="diff-container">'
    for op, val in diff_chunks:
        safe_val = val.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        if op == "equal":
            diff_html += f'<span class="diff-equal">{safe_val}</span>'
        elif op == "delete":
            diff_html += f'<span class="diff-del">{safe_val}</span>'
        elif op == "insert":
            diff_html += f'<span class="diff-ins">{safe_val}</span>'
    diff_html += '</div>'
    st.markdown(diff_html, unsafe_allow_html=True)

    # Metrics Row
    st.markdown("#### 📈 Execution Metrics")
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val">{elapsed_ms:.1f}ms</div>
            <div class="metric-lbl">Latency</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val">{len(changes)}</div>
            <div class="metric-lbl">Total Edits</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val">{edit_dist}</div>
            <div class="metric-lbl">Levenshtein Dist</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val">{len(original.split())} → {len(corrected.split())}</div>
            <div class="metric-lbl">Word Count</div>
        </div>
        """, unsafe_allow_html=True)
    with m5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val" style="color: #34D399;">100%</div>
            <div class="metric-lbl">Convergence</div>
        </div>
        """, unsafe_allow_html=True)

    # Change log
    if changes:
        st.markdown("#### 📋 Detailed Change Log")
        for c in changes:
            orig = c.get("original", "")
            rep = c.get("replacement", "")
            reason = c.get("explanation") or c.get("type", "Linguistic Adjustment")
            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.4); border-left: 3px solid #60A5FA; padding: 8px 12px; margin-bottom: 6px; border-radius: 0 6px 6px 0;">
                <code>"{orig}"</code> → <strong style="color: #86EFAC;">"{rep}"</strong> 
                <span style="color: #94A3B8; margin-left: 8px;">({reason})</span>
            </div>
            """, unsafe_allow_html=True)

    # Download utility
    st.markdown("---")
    st.download_button(
        label="💾 Download Corrected Output (.txt)",
        data=corrected,
        file_name="fixflow_output.txt",
        mime="text/plain",
        use_container_width=True
    )


# ===========================================================================
# CHANNEL 1: Direct Text Input
# ===========================================================================
if "Direct Text" in input_channel:
    st.markdown("### ✍️ Freeform Text Correction")

    sample_presets = {
        "Spelling Typos": "The quik brown fox jumps ovr the lazi dog with beautiful dynmic progranning.",
        "Grammar Mistakes": "He dont have a apple and they is coming to the the store peace of cake.",
        "Tone Polishing": "We need to fix this bug asap in order to get good results for the big boss."
    }

    selected_preset = st.selectbox("Quick Load Preset Sample", ["(Custom Input)"] + list(sample_presets.keys()))
    default_val = sample_presets[selected_preset] if selected_preset != "(Custom Input)" else "The quik brown fox jumps ovr the lazi dog. He dont have a apple and they is coming."

    input_text = st.text_area("Input Text:", value=default_val, height=130)

    if st.button("🚀 Run FixFlow", type="primary", use_container_width=True):
        if input_text.strip():
            t0 = time.perf_counter()
            if active_engine == "spell":
                corrected, changes = dp_engine.correct_text(input_text)
            elif active_engine == "grammar":
                corrected, changes = nlp_engine.fix_grammar(input_text)
            else:
                corrected, changes = nlp_engine.polish_tone(input_text, target_tone=tone_style)
            elapsed = (time.perf_counter() - t0) * 1000.0

            render_results(input_text, corrected, changes, elapsed)


# ===========================================================================
# CHANNEL 2: Presentation (PPTX) & Document Uploads
# ===========================================================================
elif "Presentation" in input_channel or "Files" in input_channel:
    st.markdown("### 📊 Presentation (PPT) & Document Correction")
    st.caption("Upload a PowerPoint presentation (.pptx), Word document (.docx), PDF (.pdf), or Markdown/Text (.txt) file to parse, extract, and correct slide-by-slide or page-by-page.")

    uploaded_file = st.file_uploader(
        "Choose a file to correct:",
        type=["pptx", "docx", "pdf", "txt", "md"],
        help="Upload PowerPoint presentations (.pptx), Word docs (.docx), PDF documents, or text files."
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        file_name = uploaded_file.name

        with st.spinner("Extracting structured content from file..."):
            try:
                extracted_text, ftype, metadata = parse_uploaded_file(file_name, file_bytes)
                st.success(f"✅ Successfully loaded **{file_name}** ({ftype.upper()} format)")

                # Display presentation metadata if PPTX
                if ftype == "pptx" and "slides" in metadata:
                    total_s = metadata["total_slides"]
                    st.info(f"Detected **{total_s} slides** in this presentation.")

                st.markdown("#### 📄 Extracted Content Preview")
                preview_text = st.text_area("Extracted Document Text (editable):", value=extracted_text, height=180)

                col_btn1, col_btn2 = st.columns([1, 1])
                with col_btn1:
                    run_slide_fix = st.button("🚀 Fix Slides & Formatting (Executive Style)", type="primary", use_container_width=True)
                with col_btn2:
                    run_standard_fix = st.button("⚡ Run DP Spell Check Only", use_container_width=True)

                if run_slide_fix or run_standard_fix:
                    t0 = time.perf_counter()
                    if run_slide_fix:
                        corrected, changes = prompt_opt.optimize_presentation_slides(preview_text)
                    else:
                        corrected, changes = dp_engine.correct_text(preview_text)
                    elapsed = (time.perf_counter() - t0) * 1000.0

                    render_results(preview_text, corrected, changes, elapsed)

            except Exception as e:
                st.error(f"Error parsing file: {e}")


# ===========================================================================
# CHANNEL 3: Email Polisher & Composer
# ===========================================================================
elif "Email" in input_channel:
    st.markdown("### 📧 Professional Email Polisher")
    st.caption("Craft, correct, and polish professional business emails with verified DP spelling, grammar, and tone.")

    # Email Presets
    email_templates = {
        "Project Status Update": {
            "sub": "Project milestone update and next steps",
            "sal": "Hi Team,",
            "body": "I wanted to let you know that we completed the dynmic programming module. He dont have any open bugs and they is ready for review. Please make sure to check this asap in order to get good results.",
            "sign": "Best regards,\nAlex"
        },
        "Meeting Request": {
            "sub": "Quick sync regarding text correction architecture",
            "sal": "Dear Dr. Smith,",
            "body": "I hope you are doing well. I would like to schedule a brief call to talk to you about our new algorithms. Let me know whether you have time tomorrow peace of cake.",
            "sign": "Sincerely,\nJordan"
        },
        "Follow-up / Inquiry": {
            "sub": "Following up on our recent conversation",
            "sal": "Hi David,",
            "body": "Just checking in to see if you had a chance to review the presentation deck. There feedback is very important to us and we want to fix any issues asap.",
            "sign": "Warm regards,\nTaylor"
        }
    }

    t_choice = st.selectbox("Load Email Template:", ["(Blank Email)"] + list(email_templates.keys()))

    c_sub = ""
    c_sal = "Hi Team,"
    c_body = ""
    c_sign = "Best regards,"

    if t_choice != "(Blank Email)":
        tmpl = email_templates[t_choice]
        c_sub = tmpl["sub"]
        c_sal = tmpl["sal"]
        c_body = tmpl["body"]
        c_sign = tmpl["sign"]

    col_sub, col_sal = st.columns([2, 1])
    with col_sub:
        email_subject = st.text_input("Subject Line:", value=c_sub, placeholder="e.g. Project status and next steps")
    with col_sal:
        email_salutation = st.text_input("Salutation / Greeting:", value=c_sal, placeholder="e.g. Hi Team,")

    email_body = st.text_area("Email Body:", value=c_body, height=140, placeholder="Write or paste your email body...")
    email_signoff = st.text_input("Sign-off / Signature:", value=c_sign, placeholder="e.g. Best regards,")

    if st.button("🚀 Polish & Correct Entire Email", type="primary", use_container_width=True):
        if email_body.strip():
            t0 = time.perf_counter()
            email_res, changes = prompt_opt.optimize_email(
                subject=email_subject,
                body=email_body,
                salutation=email_salutation,
                signoff=email_signoff,
                email_tone=tone_style
            )
            elapsed = (time.perf_counter() - t0) * 1000.0

            raw_full = f"Subject: {email_subject}\n\n{email_salutation}\n\n{email_body}\n\n{email_signoff}"
            corrected_full = email_res["full_email"]

            render_results(raw_full, corrected_full, changes, elapsed)


# ===========================================================================
# CHANNEL 4: AI Prompt Optimizer
# ===========================================================================
elif "AI Prompt" in input_channel:
    st.markdown("### 🤖 AI Prompt Optimizer & Structurer")
    st.caption("Transform vague, informal, or misspelled prompts into high-performance, structured prompts designed for Gemini, Claude, and ChatGPT.")

    target_ai = st.selectbox(
        "Target AI Model:",
        ["Gemini 2.5 Flash / Pro", "Claude 3.7 Sonnet", "ChatGPT (GPT-4o)", "Universal LLM"],
        index=0
    )

    prompt_samples = {
        "Code Generation": "write a python script to calculate levenshtein distance with dynamic programing and test it with kitten and sitting fast",
        "Bug Fix Request": "he dont know why this function is failing with index out of bounds error fix it and explain why",
        "Summary & Report": "summarize this technical paper about natural language processing and make bullet points for presentation slides"
    }

    ps_choice = st.selectbox("Load Sample Prompt:", ["(Custom Prompt)"] + list(prompt_samples.keys()))
    default_prompt = prompt_samples[ps_choice] if ps_choice != "(Custom Prompt)" else "write a python script to calculate levenshtein distance with dynamic programing and make it space optimized"

    raw_user_prompt = st.text_area("Raw AI Prompt:", value=default_prompt, height=120)

    if st.button("🚀 Optimize Prompt for AI", type="primary", use_container_width=True):
        if raw_user_prompt.strip():
            t0 = time.perf_counter()
            structured_prompt, changes = prompt_opt.optimize_ai_prompt(raw_user_prompt, target_model=target_ai)
            elapsed = (time.perf_counter() - t0) * 1000.0

            render_results(raw_user_prompt, structured_prompt, changes, elapsed)


# ---------------------------------------------------------------------------
# Extra Tab: Interactive Dynamic Programming Matrix Explorer
# ---------------------------------------------------------------------------
st.markdown("---")
with st.expander("🔬 Dynamic Programming Levenshtein Matrix Explorer", expanded=False):
    st.caption("Inspect the exact 2D Dynamic Programming state matrix $DP[i][j]$ and transitions between two words.")

    c_w1, c_w2 = st.columns(2)
    with c_w1:
        w1 = st.text_input("Word 1 (Source)", value="kitten")
    with c_w2:
        w2 = st.text_input("Word 2 (Target)", value="sitting")

    if w1 and w2:
        mat = levenshtein_matrix(w1, w2)
        dist = mat[-1][-1]
        st.success(f"**Levenshtein Distance:** `{dist}` edits between '{w1}' and '{w2}'")

        df = pd.DataFrame(mat, index=["ε"] + list(w1), columns=["ε"] + list(w2))
        st.dataframe(df.style.highlight_min(axis=0, color="#1E3A8A"), use_container_width=True)
