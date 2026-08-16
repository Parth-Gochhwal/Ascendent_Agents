"""Research data models for NEXUS.

These Pydantic models define the complete research knowledge model:
Papers, Claims, Evidence, Methods, Contradictions, Gaps, etc.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


def new_id() -> str:
    return str(uuid.uuid4())[:12]


# ─── Enums ───────────────────────────────────────────────

class SessionStatus(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    DISCOVERING = "discovering"
    RANKING = "ranking"
    ANALYZING = "analyzing"
    EXTRACTING_EVIDENCE = "extracting_evidence"
    BUILDING_GRAPH = "building_graph"
    ANALYZING_CONTRADICTIONS = "analyzing_contradictions"
    SYNTHESIZING_CONSENSUS = "synthesizing_consensus"
    DETECTING_GAPS = "detecting_gaps"
    ANALYZING_NOVELTY = "analyzing_novelty"
    DESIGNING_EXPERIMENT = "designing_experiment"
    RED_TEAM = "red_team"
    AUDITING = "auditing"
    REPORT_READY = "report_ready"
    ERROR = "error"
    PAUSED = "paused"


class EvidenceConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"


class ContradictionType(str, Enum):
    AGREEMENT = "agreement"
    APPARENT_CONTRADICTION = "apparent_contradiction"
    CONTEXTUAL_DISAGREEMENT = "contextual_disagreement"
    METHODOLOGICAL_CONFLICT = "methodological_conflict"
    DIRECT_CONTRADICTION = "direct_contradiction"
    UNRESOLVED = "unresolved"


class ConsensusStatus(str, Enum):
    CONSENSUS = "consensus"
    UNCERTAIN = "uncertain"
    CONTESTED = "contested"
    UNRESOLVED = "unresolved"


class Availability(str, Enum):
    AVAILABLE = "available"
    NOT_FOUND = "not_found"
    UNCLEAR = "unclear"


class CitationRelation(str, Enum):
    CITES = "cites"
    EXTENDS = "extends"
    COMPARES = "compares"
    SUPPORTS = "supports"
    CHALLENGES = "challenges"
    USES = "uses"


class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


# ─── Core Models ─────────────────────────────────────────

class Author(BaseModel):
    name: str
    affiliation: Optional[str] = None
    orcid: Optional[str] = None


class Paper(BaseModel):
    """Core paper representation."""
    id: str = Field(default_factory=new_id)
    title: str
    authors: list[Author] = []
    year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    citation_count: Optional[int] = None
    source_provider: str = "unknown"
    source_ids: dict[str, str] = Field(default_factory=dict)  # provider -> id
    full_text_available: bool = False
    pdf_url: Optional[str] = None
    open_access: bool = False
    sections: dict[str, str] = Field(default_factory=dict)
    relevance_score: float = 0.0
    evidence_quality: float = 0.0
    research_score: float = 0.0
    score_components: dict[str, float] = Field(default_factory=dict)
    is_demo: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ResearchPlan(BaseModel):
    """Structured research plan."""
    id: str = Field(default_factory=new_id)
    normalized_question: str
    research_objective: str
    subquestions: list[str] = []
    concepts: list[str] = []
    entities: list[str] = []
    methods_of_interest: list[str] = []
    datasets_of_interest: list[str] = []
    metrics_of_interest: list[str] = []
    search_queries: list[str] = []
    synonyms: dict[str, list[str]] = Field(default_factory=dict)
    related_terms: list[str] = []
    required_evidence_types: list[str] = []
    search_strategy: str = ""
    expected_dimensions: list[str] = []


class Claim(BaseModel):
    """An atomic research claim extracted from a paper."""
    id: str = Field(default_factory=new_id)
    paper_id: str
    statement: str
    conditions: list[str] = []
    metric: Optional[str] = None
    evidence_value: Optional[str] = None
    comparison_value: Optional[str] = None
    confidence: EvidenceConfidence = EvidenceConfidence.MEDIUM
    source_section: Optional[str] = None
    source_page: Optional[int] = None


class Evidence(BaseModel):
    """Evidence supporting or challenging a claim."""
    id: str = Field(default_factory=new_id)
    claim_id: str
    paper_id: str
    evidence_type: str = "empirical"  # empirical, theoretical, observational
    description: str
    quantitative_value: Optional[str] = None
    metric: Optional[str] = None
    dataset: Optional[str] = None
    conditions: list[str] = []
    confidence: EvidenceConfidence = EvidenceConfidence.MEDIUM
    source_location: Optional[str] = None


class MethodPipeline(BaseModel):
    """Structured method representation."""
    id: str = Field(default_factory=new_id)
    paper_id: str
    dataset: Optional[str] = None
    preprocessing: list[str] = []
    feature_engineering: list[str] = []
    model_architecture: Optional[str] = None
    model_details: Optional[str] = None
    training_procedure: Optional[str] = None
    loss_function: Optional[str] = None
    optimizer: Optional[str] = None
    baselines: list[str] = []
    metrics: list[str] = []
    evaluation_protocol: Optional[str] = None


class PaperAnalysis(BaseModel):
    """Deep analysis of a paper."""
    id: str = Field(default_factory=new_id)
    paper_id: str
    research_problem: Optional[str] = None
    research_question: Optional[str] = None
    hypothesis: Optional[str] = None
    main_findings: list[str] = []
    secondary_findings: list[str] = []
    limitations: list[str] = []
    assumptions: list[str] = []
    future_work: list[str] = []
    code_availability: Availability = Availability.UNCLEAR
    dataset_availability: Availability = Availability.UNCLEAR
    reproducibility_indicators: dict[str, Any] = Field(default_factory=dict)
    methods: list[MethodPipeline] = []
    claims: list[Claim] = []
    evidence: list[Evidence] = []


class CitationEdge(BaseModel):
    """Citation relationship between papers."""
    source_paper_id: str
    target_paper_id: str
    relation: CitationRelation = CitationRelation.CITES
    context: Optional[str] = None


class Contradiction(BaseModel):
    """A detected contradiction or disagreement between papers."""
    id: str = Field(default_factory=new_id)
    claim_a_id: str
    claim_b_id: str
    paper_a_id: str
    paper_b_id: str
    paper_a_summary: str = ""
    paper_b_summary: str = ""
    claim_a_text: str = ""
    claim_b_text: str = ""
    shared_conditions: list[str] = []
    different_conditions: list[str] = []
    classification: ContradictionType = ContradictionType.UNRESOLVED
    explanation: str = ""
    confidence: EvidenceConfidence = EvidenceConfidence.MEDIUM


class ConsensusFinding(BaseModel):
    """A finding with consensus status."""
    id: str = Field(default_factory=new_id)
    statement: str
    status: ConsensusStatus
    supporting_paper_ids: list[str] = []
    supporting_evidence: list[str] = []
    dissenting_paper_ids: list[str] = []
    confidence: EvidenceConfidence = EvidenceConfidence.MEDIUM
    explanation: str = ""


class ResearchGap(BaseModel):
    """An identified research gap."""
    id: str = Field(default_factory=new_id)
    title: str
    description: str
    gap_type: str = "underexplored"  # underexplored, conflicting, missing, methodological
    evidence: list[str] = []
    supporting_paper_ids: list[str] = []
    confidence: EvidenceConfidence = EvidenceConfidence.MEDIUM
    potential_direction: Optional[str] = None
    why_it_matters: Optional[str] = None


class NoveltyAssessment(BaseModel):
    """Novelty analysis of a proposed research idea."""
    id: str = Field(default_factory=new_id)
    proposed_idea: str = ""
    closest_papers: list[str] = []  # paper IDs
    semantic_similarity_scores: dict[str, float] = Field(default_factory=dict)
    methodological_overlap: list[str] = []
    explored_dimensions: list[str] = []
    potentially_unexplored: list[str] = []
    assessment: str = "unclear"  # potentially_promising, substantial_overlap, unclear, likely_well_explored
    explanation: str = ""
    warnings: list[str] = []


class ExperimentProposal(BaseModel):
    """A proposed experiment design."""
    id: str = Field(default_factory=new_id)
    gap_id: Optional[str] = None
    hypothesis: str
    research_objective: str
    datasets: list[str] = []
    train_test_split: Optional[str] = None
    experimental_variables: list[str] = []
    baseline_models: list[str] = []
    proposed_method: str = ""
    evaluation_metrics: list[str] = []
    ablation_studies: list[str] = []
    statistical_tests: list[str] = []
    expected_outcomes: list[str] = []
    failure_criteria: list[str] = []
    reproducibility_requirements: list[str] = []


class AuditResult(BaseModel):
    """Research integrity audit result."""
    id: str = Field(default_factory=new_id)
    total_claims: int = 0
    claims_with_evidence: int = 0
    unsupported_claims: int = 0
    citations_verified: int = 0
    citations_total: int = 0
    contradictions_represented: bool = False
    bibliography_validated: bool = False
    uncertainty_levels_present: bool = False
    issues: list[str] = []
    warnings: list[str] = []
    overall_integrity: str = "pending"  # passed, warnings, failed, pending


class RedTeamResult(BaseModel):
    """Red team analysis result."""
    id: str = Field(default_factory=new_id)
    conclusion_challenged: str
    challenges: list[str] = []
    weak_evidence: list[str] = []
    potential_biases: list[str] = []
    missing_perspectives: list[str] = []
    overgeneralizations: list[str] = []
    final_confidence: EvidenceConfidence = EvidenceConfidence.MEDIUM
    adjudication: str = ""


class MissingExperiment(BaseModel):
    """A potentially missing experiment combination."""
    id: str = Field(default_factory=new_id)
    method: str
    dataset: str
    condition: Optional[str] = None
    existing_coverage: list[str] = []  # paper IDs that do adjacent experiments
    explanation: str = ""


class AgentEvent(BaseModel):
    """An event from agent execution."""
    id: str = Field(default_factory=new_id)
    session_id: str
    agent_name: str
    status: AgentStatus
    message: str = ""
    detail: Optional[str] = None
    progress: Optional[float] = None  # 0-1
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None
    token_usage: Optional[int] = None


class SearchResult(BaseModel):
    """Result from a search query."""
    query: str
    provider: str
    papers_found: int = 0
    paper_ids: list[str] = []


class ResearchSession(BaseModel):
    """Complete research session state."""
    id: str = Field(default_factory=new_id)
    title: str = ""
    question: str
    status: SessionStatus = SessionStatus.IDLE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    plan: Optional[ResearchPlan] = None
    searches: list[SearchResult] = []
    papers: dict[str, Paper] = Field(default_factory=dict)  # id -> Paper
    analyses: dict[str, PaperAnalysis] = Field(default_factory=dict)  # paper_id -> PaperAnalysis
    claims: list[Claim] = []
    evidence: list[Evidence] = []
    methods: list[MethodPipeline] = []
    citations: list[CitationEdge] = []
    contradictions: list[Contradiction] = []
    consensus: list[ConsensusFinding] = []
    gaps: list[ResearchGap] = []
    missing_experiments: list[MissingExperiment] = []
    novelty: Optional[NoveltyAssessment] = None
    experiment: Optional[ExperimentProposal] = None
    red_team: Optional[RedTeamResult] = None
    audit: Optional[AuditResult] = None
    agent_events: list[AgentEvent] = []
    stats: dict[str, Any] = Field(default_factory=dict)
    is_demo: bool = False

    def add_event(self, agent_name: str, status: AgentStatus, message: str = "",
                  detail: str = None, progress: float = None) -> AgentEvent:
        event = AgentEvent(
            session_id=self.id,
            agent_name=agent_name,
            status=status,
            message=message,
            detail=detail,
            progress=progress,
        )
        self.agent_events.append(event)
        self.updated_at = datetime.utcnow()
        return event

    def update_stats(self):
        self.stats = {
            "papers_discovered": len(self.papers),
            "papers_analyzed": len(self.analyses),
            "claims_extracted": len(self.claims),
            "evidence_items": len(self.evidence),
            "methods_extracted": len(self.methods),
            "contradictions_found": len(self.contradictions),
            "consensus_findings": len(self.consensus),
            "research_gaps": len(self.gaps),
            "missing_experiments": len(self.missing_experiments),
            "citations_mapped": len(self.citations),
        }


class WhyEvidenceChainItem(BaseModel):
    """Traceable evidence item in the 'Why?' reasoning chain."""
    claim: str
    evidence: str
    source_paper_id: str
    source_paper_title: str
    source_location: Optional[str] = None
    doi_or_url: Optional[str] = None
    confidence: EvidenceConfidence = EvidenceConfidence.MEDIUM


class WhyExplanation(BaseModel):
    """Detailed explainability model for AI-generated conclusions."""
    id: str = Field(default_factory=new_id)
    target_type: str  # 'contradiction' | 'consensus' | 'gap' | 'paper' | 'novelty' | 'red_team'
    target_id: str
    target_statement: str
    confidence: EvidenceConfidence = EvidenceConfidence.MEDIUM
    evidence_chain: list[WhyEvidenceChainItem] = []
    reasoning_factors: list[str] = []
    uncertainty_analysis: str = ""
    conflicting_evidence: list[str] = []
    counter_hypotheses: list[str] = []


class TimelineMilestone(BaseModel):
    """Longitudinal milestone in the research landscape."""
    year: int
    paradigm: str
    title: str
    description: str
    paper_ids: list[str] = []
    key_methods: list[str] = []
    breakthrough_indicator: bool = False

