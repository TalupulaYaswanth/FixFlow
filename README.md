# ⚡ FixFlow: Smart Text Correction Powered by Dynamic Programming & NLP

FixFlow is a high-performance text correction and linguistic enhancement system combining classical **Dynamic Programming (DP)** algorithms with modern **Natural Language Processing (NLP)** and Large Language Models.

---

## 🌟 Key Features

1. **Space-Optimized Levenshtein Distance ($O(\min(m, n))$ space)**
   - Calculates minimal edit operations (insertions, deletions, substitutions).
   - Uses a 2-row rolling buffer, reducing memory overhead from quadratic to linear.
2. **Top-K Spelling Suggestion Engine**
   - Ranks vocabulary candidates by minimum edit distance and logarithmic word frequency.
   - Fast bounding pruning ($|len(w_1) - len(w_2)| \le k$).
3. **LCS (Longest Common Subsequence) Diff Visualizer**
   - Word-level DP diff matrix with backtracking to compute additions, deletions, and matches.
4. **Viterbi Algorithm for Context Disambiguation**
   - Context-aware sequence decoder using Bigram state transitions (e.g. *piece of cake* vs *peace of cake*).
5. **Rule-Based & Heuristic NLP Engine**
   - Subject-verb agreement, indefinite articles (*a* vs *an*), contractions, and punctuation without external dependencies.
6. **Multi-Tone Polishing Engine**
   - Formal, Professional, Casual, and Concise stylistic transforms.
   - Optional plug-and-play **Google GenAI SDK (Gemini)** integration.
7. **Interactive Streamlit Web Studio & FastAPI Backend**
   - Side-by-side color-coded diff highlights, execution metrics (latency, edit distance, convergence), and interactive DP matrix explorer.

---

## 📐 Dynamic Programming Formulations

### 1. Levenshtein Distance (Edit Distance)
Let $DP[i][j]$ denote the minimum edit distance between prefixes $A[0..i-1]$ and $B[0..j-1]$:

$$DP[i][j] = \begin{cases} 
i & \text{if } j = 0 \\
j & \text{if } i = 0 \\
DP[i-1][j-1] & \text{if } A[i-1] = B[j-1] \\
1 + \min\big(DP[i-1][j], DP[i][j-1], DP[i-1][j-1]\big) & \text{otherwise}
\end{cases}$$

**Space Optimization:** Because computing row $i$ only requires row $i-1$, FixFlow maintains two alternating arrays (`previous_row` and `current_row`), reducing space complexity from $O(m \cdot n)$ to $O(\min(m, n))$.

---

### 2. Longest Common Subsequence (LCS) for Visual Diffs
For token sequences $A$ (original) and $B$ (corrected):

$$LCS[i][j] = \begin{cases}
0 & \text{if } i = 0 \text{ or } j = 0 \\
LCS[i-1][j-1] + 1 & \text{if } A[i-1] = B[j-1] \\
\max\big(LCS[i-1][j], LCS[i][j-1]\big) & \text{if } A[i-1] \neq B[j-1]
\end{cases}$$

Backtracking from $(m, n)$ yields:
- `A[i-1] == B[j-1]`: Unchanged token (`equal`)
- `LCS[i][j-1] >= LCS[i-1][j]`: Insertion from corrected string (`insert`)
- `LCS[i-1][j] > LCS[i][j-1]`: Deletion from original string (`delete`)

---

## 🚀 Quickstart & Usage

### 1. Run the Streamlit Interactive Studio
Launch the browser UI:
```bash
streamlit run app.py
```
Open your browser to: `http://localhost:8501`

### 2. Run the FastAPI REST Server
Start the high-performance backend:
```bash
uvicorn main:app --reload --port 8000
```
- Interactive Swagger API docs: `http://localhost:8000/docs`
- Redoc documentation: `http://localhost:8000/redoc`

### 3. Run the Test Suite
Verify all DP algorithms, grammar heuristics, and endpoints:
```bash
python test_fixflow.py
```

---

## 📡 REST API Reference

### `POST /correct`
Corrects text using the specified engine.
```json
{
  "text": "The quik brown fox jumps ovr the lazi dog.",
  "mode": "spell"
}
```
**Response:**
```json
{
  "original_text": "The quik brown fox jumps ovr the lazi dog.",
  "corrected_text": "The quick brown fox jumps over the lazy dog.",
  "mode": "spell",
  "changes": [...],
  "diff": [
    {"type": "equal", "text": "The "},
    {"type": "delete", "text": "quik"},
    {"type": "insert", "text": "quick"},
    {"type": "equal", "text": " brown fox jumps "},
    {"type": "delete", "text": "ovr"},
    {"type": "insert", "text": "over"},
    {"type": "equal", "text": " the "},
    {"type": "delete", "text": "lazi"},
    {"type": "insert", "text": "lazy"},
    {"type": "equal", "text": " dog."}
  ],
  "metrics": {
    "processing_time_ms": 3.4,
    "total_edits": 3,
    "levenshtein_distance": 4
  }
}
```

### `POST /suggestions`
Generates top-K candidates for an isolated word using Levenshtein distance:
```json
{
  "word": "progranning",
  "k": 3
}
```

### `POST /optimize/email`
Polishes email drafts (Subject, Salutation, Body, Sign-off) with tone adjustments:
```json
{
  "subject": "project update and dynmic programing",
  "body": "he dont have time to review this asap in order to get good results",
  "salutation": "Hi Team,",
  "signoff": "Best regards,",
  "tone": "professional"
}
```

### `POST /optimize/ai-prompt`
Structures raw prompts for Gemini, Claude, or ChatGPT into production-grade prompts:
```json
{
  "raw_prompt": "write a python script with dynmic programing",
  "target_model": "Gemini 2.5"
}
```

### `POST /upload-file`
Accepts `.pptx`, `.docx`, `.pdf`, `.txt` files, extracts content, and corrects slide-by-slide or section-by-section.

---

## 📁 Repository Structure
```
├── .github/
│   ├── workflows/
│   │   └── ci.yml           # GitHub Actions CI workflow
│   ├── ISSUE_TEMPLATE/      # Bug report & feature request templates
│   └── PULL_REQUEST_TEMPLATE.md
├── frontend/                # Modern Single-Page Application (HTML5 / CSS3 / Vanilla JS)
│   ├── index.html           # FixFlow Web UI
│   ├── style.css            # Dark/light theme styles & responsive design
│   └── app.js               # Frontend controller, API bridge & diff visualization
├── dp_corrector.py          # Space-optimized Levenshtein, Top-K vocab ranker, LCS diff, Viterbi
├── nlp_corrector.py         # Rule-based grammar/syntax, tone polishers, Google GenAI SDK fallback
├── document_parser.py       # PowerPoint (.pptx), Word (.docx), PDF (.pdf), and text file parser
├── prompt_optimizer.py      # AI prompt structurer, executive email polisher, slide deck optimizer
├── main.py                  # FastAPI REST backend with all correction and optimization endpoints
├── app.py                   # Streamlit Studio with 4 input channels (Direct, PPT/Files, Email, AI Prompt)
├── test_fixflow.py          # Complete automated test suite (100% passing)
├── requirements.txt         # Python dependencies
├── .env.example             # Template for environment variables (Gemini API key, ports)
├── .gitignore               # Comprehensive Git ignore rules
├── CONTRIBUTING.md          # Contribution guidelines
├── SECURITY.md              # Security policy & vulnerability reporting
├── LICENSE                  # MIT License
└── README.md                # Documentation & DP algorithmic formulations
```

---

## 🛠️ Environment Configuration

Copy `.env.example` to `.env` to configure optional features such as the Google Gemini API key:
```bash
cp .env.example .env
```

---

## 🌐 Standalone Frontend Web App

In addition to the Streamlit Studio, FixFlow includes a standalone frontend interface located in `frontend/`:
1. Start the FastAPI backend:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
2. Open `frontend/index.html` in your web browser or serve it via any static file server:
   ```bash
   python -m http.server 3000 --directory frontend
   ```
3. Navigate to `http://localhost:3000`.

---

## 📄 License
This project is open-source and licensed under the [MIT License](LICENSE).


