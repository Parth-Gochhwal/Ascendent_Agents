# Ascendent Agents (NEXUS) — Quick Start & Operator Guide

Welcome! NEXUS is an autonomous evidence-driven scientific research workstation that transforms arbitrary research questions into structured literature discovery, full-text open-access evidence analysis, contradiction detection, gap discovery, and experiment protocols.

---

## ⚡ Quick Diagnostic Check

To verify all provider connections, LLM configuration, and the PyMuPDF full-text engine:

```powershell
python backend/scripts/smoke_test.py
```

---

## 🚀 Running the Project

### Terminal 1: Backend Server

From the repository root:
```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.app.main:app --reload --port 8000
```

### Terminal 2: Frontend Client

In a separate terminal window:
```powershell
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser. API docs are available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

## ⚙️ Operating Modes

### 1. Demo Mode (`DEMO_MODE=true` in `.env`)
- Default mode for rapid hackathon evaluations.
- Instant, deterministic execution using a curated battery degradation benchmark corpus.
- Requires no external API keys or network calls.

### 2. Live Academic Mode (`DEMO_MODE=false` in `.env`)
- Executes live multi-provider discovery across **OpenAlex**, **Crossref**, **arXiv**, and **Semantic Scholar**.
- Automatically fetches legitimate **Open-Access (OA) full-text PDFs** (arXiv, unpaywalled publishers), extracts text with **PyMuPDF**, detects scholarly sections (Methods, Results, Limitations), and grounds all extracted claims and evidence.
- Driven by **Google Gemini** (`gemini-3.7-flash` for reasoning, `gemini-3.5-flash-lite` for fast tasks).

Configure `.env`:
```env
DEMO_MODE=false
GEMINI_API_KEY=your_gemini_api_key_here
OPENALEX_EMAIL=your_email@example.com
OPENALEX_API_KEY=optional_key_for_higher_limits
SEMANTIC_SCHOLAR_API_KEY=optional_key
CROSSREF_EMAIL=your_email@example.com
```

---

## 🧪 Testing & Verification

Run the full automated test suite (101 unit/integration tests):
```powershell
python -m pytest backend/tests/ -v
```

Run live question-independence verification (tests Question A vs Question B):
```powershell
python backend/scripts/verify_questions.py
```

Validate frontend build and linting:
```powershell
cd frontend
npm run build
npm run lint
```
