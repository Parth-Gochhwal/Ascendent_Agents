# NEXUS — AI Research Scientist

> "From What Do We Know? to What Should We Investigate Next?"

NEXUS is an autonomous evidence-driven research agent that discovers academic literature, reconstructs the evidence landscape, identifies contradictions and research gaps, evaluates proposed research ideas, and designs the next experiment.

Built for **Track 04 — AI Academic Research Assistant** at the Ascendant Agents Generative AI Hackathon.

## ✨ Features

- **Research Planning**: Decomposes questions into subquestions, concepts, and multi-source search strategies
- **Multi-Source Literature Discovery**: OpenAlex, Semantic Scholar, Crossref, arXiv
- **Intelligent Deduplication & Ranking**: DOI/title normalization with composite research scoring
- **Deep Paper Analysis**: Structured extraction of findings, methods, limitations
- **Evidence Extraction**: Atomic claims with traceable evidence chains
- **Contradiction Engine**: Context-aware scientific disagreement analysis (not simple text matching)
- **Consensus Analysis**: Determines agreement, contested, and unresolved findings
- **Research Gap Detection**: Evidence-driven gap identification with potential directions
- **Novelty Analyzer**: Evaluates proposed ideas against existing literature
- **Experiment Designer**: Generates concrete experimental protocols
- **Red Team Review**: Challenges conclusions for robustness
- **Research Integrity Audit**: Automated claim-evidence verification
- **Interactive Citation Graph**: Visualize paper relationships
- **Research Dossier**: Complete structured report generation
- **"WHY?" System**: Every conclusion is traceable to evidence
- **Demo Mode**: Full functionality with synthetic corpus for reliable demos

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- (Optional) Google Gemini API key for live mode

### Setup

```bash
# Clone the repository
cd D:\Ascendent_Agents

# Create and activate virtual environment (Windows)
python -m venv .venv
.venv\Scripts\activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..

# Create .env (or use the provided one for demo mode)
copy .env.example .env
```

### Run

**Option 1: Startup script**
```bash
start.bat
```

**Option 2: Manual**
```bash
# Terminal 1: Backend
.venv\Scripts\activate
python -m uvicorn backend.app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

Open http://localhost:5173

### Demo Mode

By default, NEXUS runs in demo mode (`DEMO_MODE=true` in `.env`). This uses a curated synthetic research corpus demonstrating all features without requiring API keys.

### Live Mode

To use real academic APIs and Gemini:

```env
DEMO_MODE=false
GEMINI_API_KEY=your_key_here
OPENALEX_EMAIL=your@email.com
```

## 🏗 Architecture

```
User → Research Workspace → Planner → Literature Discovery
  → Deduplication → Paper Intelligence → Evidence Extraction
  → Knowledge Graph → Contradiction Engine → Consensus Engine
  → Gap Detector → Novelty Analyzer → Experiment Designer
  → Red Team → Integrity Auditor → Research Dossier
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

## 📁 Project Structure

```
D:/Ascendent_Agents/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes, WebSocket
│   │   ├── core/         # Configuration
│   │   ├── models/       # Pydantic research models
│   │   ├── providers/    # LLM + Academic search providers
│   │   ├── prompts/      # Versioned prompt templates
│   │   └── services/     # Pipeline, demo data
│   └── tests/            # Test suite
├── frontend/
│   └── src/              # React + TypeScript application
├── data/                 # Runtime data (gitignored)
├── docs/                 # Architecture documentation
├── .env.example          # Environment template
├── .gitignore
├── start.bat             # One-click launcher
└── README.md
```

## 🔬 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEMO_MODE` | Use synthetic corpus | `true` |
| `GEMINI_API_KEY` | Google Gemini API key | - |
| `GEMINI_MODEL` | Primary model | `gemini-2.0-flash` |
| `GEMINI_FAST_MODEL` | Fast/cheap model | `gemini-2.0-flash-lite` |
| `OPENALEX_EMAIL` | OpenAlex polite pool | - |
| `SEMANTIC_SCHOLAR_API_KEY` | S2 API key | - |
| `CROSSREF_EMAIL` | Crossref polite pool | - |
| `MAX_PAPERS_DEEP_ANALYSIS` | Max papers for deep analysis | `15` |
| `LLM_RATE_LIMIT_PER_MINUTE` | LLM rate limit | `30` |

## 🧪 Testing

```bash
.venv\Scripts\activate
pytest backend/tests/ -v
```

## 📊 Demo Scenario

The default demo demonstrates the research question:

> "Are graph neural networks genuinely better than transformer-based models for battery remaining useful life prediction under cross-domain conditions?"

The demo corpus includes 8 synthetic papers specifically designed to showcase:
- Methodological agreement
- Contextual disagreement (different datasets/conditions)
- Apparent contradictions
- Research gaps (missing experiments)
- Method comparison across architectures

## 🔒 Security

- API keys are server-side only
- No secrets in frontend
- Input validation on all endpoints
- Upload size limits
- No arbitrary code execution

## 📝 License

Hackathon project — [MIT License]
