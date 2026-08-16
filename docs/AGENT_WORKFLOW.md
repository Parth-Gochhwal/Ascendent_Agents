# NEXUS Multi-Agent Research Workflow

## Overview of the Agent Execution Pipeline

NEXUS executes research through a sequential and feedback-governed pipeline of specialized agents. Rather than passing unconstrained conversational text between models, agents communicate through typed, validated Pydantic data structures.

---

## Agent Step-by-Step Breakdown

### Phase 1: Research Planner (`Agent 1`)
- **Input**: Natural-language scientific question.
- **Process**:
  1. Normalizes the research question into clear, canonical scientific terminology.
  2. Decomposes the primary question into 5–8 focused subquestions.
  3. Extracts domain entities, candidate architectures, benchmark datasets, and evaluation metrics.
  4. Formulates a multi-angle search strategy with 8–12 diverse queries.
- **Output**: `ResearchPlan`

---

### Phase 2: Literature Discovery (`Agent 2`)
- **Input**: `ResearchPlan.search_queries`
- **Process**:
  1. Queries multiple academic adapters (OpenAlex, Semantic Scholar, Crossref, arXiv) asynchronously.
  2. Extracts abstracts, titles, authors, venues, years, DOIs, open-access status, and citation counts.
  3. Emits stage progress events for live UI visibility.
- **Output**: Raw candidate `list[Paper]`

---

### Phase 3: Relevance Engine & Deduplication (`Agent 3`)
- **Input**: Raw candidate papers.
- **Process**:
  1. DOI canonicalization and alphanumeric title normalization.
  2. Duplicate detection and merging across disparate providers.
  3. Multi-factor scoring:
     $$\text{Score} = 0.35 \cdot \text{Relevance} + 0.25 \cdot \text{Recency} + 0.20 \cdot \text{Citation} + 0.20 \cdot \text{Completeness}$$
  4. Selection of top $N$ papers for deep analysis.
- **Output**: Ranked, deduplicated `dict[str, Paper]`

---

### Phase 4: Paper Intelligence (`Agent 4`)
- **Input**: Selected high-ranking papers.
- **Process**:
  1. Deeply analyzes abstract and paper sections.
  2. Extracts research problem, hypothesis, main findings, limitations, assumptions, and future directions.
  3. Evaluates reproducibility indicators (code availability, dataset availability).
- **Output**: `dict[str, PaperAnalysis]`

---

### Phase 5: Evidence & Method Extraction (`Agents 5 & 6`)
- **Input**: `PaperAnalysis` records.
- **Process**:
  1. Deconstructs findings into atomic `Claim` entities with explicit experimental conditions and quantitative values.
  2. Creates linked `Evidence` entities referencing source locations and confidence levels.
  3. Constructs structured `MethodPipeline` records (Preprocessing $\rightarrow$ Feature Engineering $\rightarrow$ Model $\rightarrow$ Loss $\rightarrow$ Evaluation).
- **Output**: `list[Claim]`, `list[Evidence]`, `list[MethodPipeline]`

---

### Phase 6: Citation Intelligence (`Agent 7`)
- **Input**: Analyzed papers and claims.
- **Process**:
  1. Maps relationships between papers (`cites`, `extends`, `compares`, `challenges`, `supports`).
  2. Builds graph topology for interactive SVG rendering.
- **Output**: `list[CitationEdge]`

---

### Phase 7: Contradiction Engine (`Agent 8`)
- **Input**: Pairwise claims from different papers.
- **Process**:
  1. Evaluates whether disagreements are direct or contextual.
  2. Performs condition differential analysis:
     - Shared conditions (e.g., both evaluate battery RUL)
     - Differing conditions (e.g., NMC vs. LFP, 30 cycles vs. 100 cycles, single-cell vs. multi-cell)
  3. Classifies relation: `Agreement`, `Apparent Contradiction`, `Contextual Disagreement`, `Methodological Conflict`, `Direct Contradiction`, or `Unresolved`.
- **Output**: `list[Contradiction]`

---

### Phase 8: Consensus Engine (`Agent 9`)
- **Input**: Aggregated claims across the literature.
- **Process**:
  1. Identifies broad areas of convergence and controversy.
  2. Classifies findings into `Consensus`, `Contested`, or `Uncertain`.
  3. Links supporting and dissenting paper IDs to each finding.
- **Output**: `list[ConsensusFinding]`

---

### Phase 9: Gap Detector & Missing Experiments (`Agent 10`)
- **Input**: Literature claims, limitations, contradictions, and method/dataset matrix.
- **Process**:
  1. Discovers systemic blind spots (e.g., lack of cross-domain evaluation, missing baseline ablations).
  2. Detects Cartesian evaluation holes (e.g., Architecture X never tested on Benchmark Y).
  3. Formulates potential research directions grounded strictly in retrieved evidence.
- **Output**: `list[ResearchGap]`, `list[MissingExperiment]`

---

### Phase 10: Novelty Analyzer (`Agent 11`)
- **Input**: Proposed research hypothesis (from user or identified gap).
- **Process**:
  1. Matches proposal against retrieved corpus.
  2. Computes methodological overlap and identifies already-explored dimensions.
  3. Highlights potentially unexplored dimensions with scientific caution.
- **Output**: `NoveltyAssessment`

---

### Phase 11: Experiment Designer (`Agent 12`)
- **Input**: Top prioritized research gap.
- **Process**:
  1. Formulates testable hypothesis and research objective.
  2. Specifies datasets, splits, variables, and baseline models.
  3. Specifies ablation studies, statistical validation tests, expected outcomes, and failure criteria.
- **Output**: `ExperimentProposal`

---

### Phase 12: Research Red Team (`Agent 14`)
- **Input**: Primary conclusions and supporting evidence.
- **Process**:
  1. Critically challenges findings (selection bias, overgeneralization, lack of independent replication).
  2. Evaluates potential confounding factors.
  3. Adjudicates final confidence ratings.
- **Output**: `RedTeamResult`

---

### Phase 13: Integrity Auditor (`Agent 15`)
- **Input**: Complete session state.
- **Process**:
  1. Verifies that claims have traceable evidence.
  2. Ensures bibliography completeness and citation validity.
  3. Computes final integrity status (`passed`, `warnings`, `failed`).
- **Output**: `AuditResult` and compiled `Research Dossier`
