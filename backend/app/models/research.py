"""Research data models for NEXUS.

These Pydantic models define the complete research knowledge model:
Papers, Claims, Evidence, Methods, Contradictions, Gaps, Dead Ends,
ClaimLine, Citation Echo, Reproducibility, Evidence Strength, etc.
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
    ANALYZING_DEAD_ENDS = "analyzing_dead_ends"
    CHECKING_REPRODUCIBILITY = "checking_reproducibility"
    ANALYZING_NOVELTY = "analyzing_novelty"
    DESIGNING_EXPERIMENT = "designing_experiment"
    RED_TEAM = "red_team"
    AUDITING = "auditing"
    SYNTHESIZING = "synthesizing"
    REPORT_READY = "report_ready"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    ERROR = "error"
    PAUSED = "paused"


class EvidenceConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"
    INSUFFICIENT = "insufficient"


class ContradictionType(str, Enum):
    AGREEMENT = "agreement"
    APPARENT_CONTRADICTION = "apparent_contradiction"
    CONTEXTUAL_DISAGREEMENT = "contextual_disagreement"
    METHODOLOGICAL_CONFLICT = "methodological_conflict"
    METRIC_DISAGREEMENT = "metric_disagreement"
    SCOPE_DISAGREEMENT = "scope_disagreement"
    DIRECT_CONTRADICTION = "direct_contradiction"
    METHOD_VARIATION = "method_variation"
    INSUFFICIENT_INFORMATION = "insufficient_information"
    UNRESOLVED = "unresolved"


class ConsensusStatus(str, Enum):
    SUPPORTED = "supported"
    LIKELY_SUPPORTED = "likely_supported"
    CONSENSUS = "consensus"  # backward compat
    MIXED = "mixed"
    CONTESTED = "contested"
    UNCERTAIN = "uncertain"
    UNRESOLVED = "unresolved"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class Availability(str, Enum):
    AVAILABLE = "available"
    PARTIAL = "partial"
    NOT_FOUND = "not_found"
    UNAVAILABLE = "unavailable"
    UNCLEAR = "unclear"
    UNKNOWN = "unknown"


class CitationRelation(str, Enum):
    CITES = "cites"
    EXTENDS = "extends"
    COMPARES = "compares"
    SUPPORTS = "supports"
    CHALLENGES = "challenges"
    USES = "uses"
    DERIVES_FROM = "derives_from"
    GENERALIZES = "generalizes"
    SPECIALIZES = "specializes"
    CONTRADICTS = "contradicts"


class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ClaimPropagationType(str, Enum):
    """How a claim changed as it propagated through literature."""
    PRESERVED = "preserved"
    WEAKENED = "weakened"
    STRENGTHENED = "strengthened"
    GENERALIZED = "generalized"
    SPECIALIZED = "specialized"
    CONTEXT_SHIFTED = "context_shifted"
    CONTRADICTED = "contradicted"
    UNSUPPORTED_EXTENSION = "unsupported_extension"


class DeadEndStatus(str, Enum):
    FAILED = "failed"
    LIMITED = "limited"
    NON_GENERALIZING = "non_generalizing"
    SUPERSEDED = "superseded"
    UNRESOLVED = "unresolved"
    PROMISING_BUT_UNDERTESTED = "promising_but_undertested"


class GapDimension(str, Enum):
    DATA = "data"
    DOMAIN = "domain"
    GENERALIZATION = "generalization"
    METHODOLOGY = "methodology"
    EVALUATION = "evaluation"
    REPRODUCIBILITY = "reproducibility"
    THEORY = "theory"
    BASELINE = "baseline"
    UNCERTAINTY = "uncertainty"
    DEPLOYMENT = "deployment"
    SCALABILITY = "scalability"
    CAUSALITY = "causality"


class NoveltyLevel(str, Enum):
    NOVEL = "novel"
    POTENTIALLY_NOVEL = "potentially_novel"
    INCREMENTAL = "incremental"
    OVERLAPPING = "overlapping"
    ALREADY_EXPLORED = "already_explored"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class IntegrityVerdict(str, Enum):
    PASS = "pass"
    PASS_WITH_WARNINGS = "pass_with_warnings"
    FAIL = "fail"


class RedTeamFindingType(str, Enum):
    UNSUPPORTED_CLAIM = "unsupported_claim"
    CITATION_MISUSE = "citation_misuse"
    CHERRY_PICKING = "cherry_picking"
    HIDDEN_ASSUMPTION = "hidden_assumption"
    DATASET_BIAS = "dataset_bias"
    PUBLICATION_BIAS = "publication_bias"
    SURVIVORSHIP_BIAS = "survivorship_bias"
    DUPLICATED_EVIDENCE = "duplicated_evidence"
    CITATION_ECHO = "citation_echo"
    CONTEXTUAL_MISMATCH = "contextual_mismatch"
    OVERGENERALIZATION = "overgeneralization"
    WEAK_BASELINE = "weak_baseline"
    EVALUATION_LEAKAGE = "evaluation_leakage"
    CONTRADICTORY_EVIDENCE_IGNORED = "contradictory_evidence_ignored"
    INSUFFICIENT_SAMPLE = "insufficient_sample"
    REPRODUCIBILITY_WEAKNESS = "reproducibility_weakness"
    FALSE_NOVELTY = "false_novelty"
    SPECULATIVE_AS_FACT = "speculative_as_fact"


class RedTeamSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


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
    relevance_score: Optional[float] = None
    evidence_quality: Optional[float] = None
    research_score: Optional[float] = None
    score_components: dict[str, float] = Field(default_factory=dict)
    is_demo: bool = False
    retrieved_at: Optional[datetime] = None
    metadata_quality: Optional[float] = None
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


# ─── Evidence Strength Model ─────────────────────────────

class EvidenceStrength(BaseModel):
    """Multi-dimensional evidence assessment — replaces single confidence score."""
    directness: float = 0.5  # 0-1: how directly does evidence support the claim
    source_quality: float = 0.5  # 0-1: venue quality, peer review status
    methodological_rigor: float = 0.5  # 0-1: experimental design quality
    reproducibility: float = 0.5  # 0-1: can others replicate this?
    external_validity: float = 0.5  # 0-1: generalizes beyond tested conditions?
    cross_study_consistency: float = 0.5  # 0-1: agrees with other studies?
    scope_alignment: float = 0.5  # 0-1: claim scope matches evidence scope?
    overall_assessment: EvidenceConfidence = EvidenceConfidence.MEDIUM
    rationale: str = ""

    @property
    def composite_score(self) -> float:
        """Deterministic weighted composite from sub-dimensions."""
        return round(
            0.20 * self.directness +
            0.15 * self.source_quality +
            0.20 * self.methodological_rigor +
            0.15 * self.reproducibility +
            0.10 * self.external_validity +
            0.10 * self.cross_study_consistency +
            0.10 * self.scope_alignment,
            3
        )


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
    strength: Optional[EvidenceStrength] = None
    source_section: Optional[str] = None
    source_page: Optional[int] = None
    status: str = "active"  # active, needs_review, invalidated, downgraded


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
    strength: Optional[EvidenceStrength] = None
    source_location: Optional[str] = None


class ClaimList(BaseModel):
    claims: list[Claim] = []


# ─── ClaimLine (Claim Propagation) ───────────────────────

class ClaimPropagation(BaseModel):
    """Tracks how a claim propagated through literature."""
    id: str = Field(default_factory=new_id)
    source_claim_id: str
    derived_claim_id: str
    source_paper_id: str
    derived_paper_id: str
    relationship_type: ClaimPropagationType = ClaimPropagationType.PRESERVED
    source_conditions: list[str] = []
    derived_conditions: list[str] = []
    evidence_strength: EvidenceConfidence = EvidenceConfidence.MEDIUM
    scope_change: str = ""  # description of how scope changed
    confidence: EvidenceConfidence = EvidenceConfidence.MEDIUM
    explanation: str = ""


# ─── Citation Echo Detection ─────────────────────────────

class CitationEchoCluster(BaseModel):
    """Detects citation echo chambers where consensus is illusory."""
    id: str = Field(default_factory=new_id)
    claim_statement: str
    originating_paper_id: str
    originating_paper_title: str = ""
    echo_paper_ids: list[str] = []  # papers that derive from originating
    total_support_count: int = 0
    independent_support_count: int = 0
    citation_dependency_depth: int = 0
    echo_chain: list[str] = []  # paper_id chain showing propagation
    independence_weight: float = 1.0  # 0-1: how independent is the support?
    explanation: str = ""


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
    is_inferred: bool = True


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
    difference_dimensions: list[str] = []  # dataset, domain, metric, etc.
    classification: ContradictionType = ContradictionType.UNRESOLVED
    explanation: str = ""
    confidence: EvidenceConfidence = EvidenceConfidence.MEDIUM
    severity: str = "medium"  # critical, high, medium, low
    resolution_status: str = "unresolved"  # resolved, partially_resolved, unresolved
    can_coexist: Optional[bool] = None  # can these findings actually coexist?
    coexistence_conditions: str = ""  # under what conditions can they coexist?


class ContradictionList(BaseModel):
    contradictions: list[Contradiction] = []


class ConsensusFinding(BaseModel):
    """A finding with consensus status."""
    id: str = Field(default_factory=new_id)
    statement: str
    status: ConsensusStatus = ConsensusStatus.UNCERTAIN
    supporting_paper_ids: list[str] = []
    supporting_evidence: list[str] = []
    dissenting_paper_ids: list[str] = []
    confidence: EvidenceConfidence = EvidenceConfidence.MEDIUM
    explanation: str = ""
    independence_weight: float = 1.0  # 0-1: accounts for citation echo
    independent_support_count: int = 0
    evidence_quality_weighted: bool = False  # was quality considered?


class ConsensusList(BaseModel):
    findings: list[ConsensusFinding] = []


# ─── Dead-End Atlas ──────────────────────────────────────

class DeadEnd(BaseModel):
    """A research approach identified as a dead end."""
    id: str = Field(default_factory=new_id)
    approach: str
    description: str
    supporting_papers: list[str] = []  # paper IDs
    failure_evidence: list[str] = []
    failure_conditions: list[str] = []
    attempt_count: int = 1
    success_conditions_if_any: list[str] = []
    confidence: EvidenceConfidence = EvidenceConfidence.MEDIUM
    status: DeadEndStatus = DeadEndStatus.UNRESOLVED
    alternative_directions: list[str] = []


# ─── Reproducibility Profile ────────────────────────────

class ReproducibilityProfile(BaseModel):
    """Reproducibility assessment for a paper or claim."""
    id: str = Field(default_factory=new_id)
    paper_id: str
    dataset_available: Availability = Availability.UNKNOWN
    data_preprocessing_documented: Availability = Availability.UNKNOWN
    code_available: Availability = Availability.UNKNOWN
    model_specification_documented: Availability = Availability.UNKNOWN
    hyperparameters_documented: Availability = Availability.UNKNOWN
    training_procedure_documented: Availability = Availability.UNKNOWN
    random_seeds_reported: Availability = Availability.UNKNOWN
    evaluation_metrics_defined: Availability = Availability.UNKNOWN
    baselines_reproducible: Availability = Availability.UNKNOWN
    statistical_reporting: Availability = Availability.UNKNOWN
    hardware_environment_documented: Availability = Availability.UNKNOWN
    external_validation: Availability = Availability.UNKNOWN
    experimental_protocol_documented: Availability = Availability.UNKNOWN
    completeness_score: float = 0.0  # deterministic from above
    missing_components: list[str] = []
    risk_factors: list[str] = []
    replication_risks: list[str] = []
    explanation: str = ""

    def compute_completeness(self) -> float:
        """Deterministically compute completeness from component availability."""
        components = [
            self.dataset_available, self.data_preprocessing_documented,
            self.code_available, self.model_specification_documented,
            self.hyperparameters_documented, self.training_procedure_documented,
            self.random_seeds_reported, self.evaluation_metrics_defined,
            self.baselines_reproducible, self.statistical_reporting,
            self.hardware_environment_documented, self.external_validation,
            self.experimental_protocol_documented,
        ]
        score_map = {
            Availability.AVAILABLE: 1.0,
            Availability.PARTIAL: 0.5,
            Availability.NOT_FOUND: 0.0,
            Availability.UNAVAILABLE: 0.0,
            Availability.UNCLEAR: 0.25,
            Availability.UNKNOWN: 0.25,
        }
        total = sum(score_map.get(c, 0.25) for c in components)
        self.completeness_score = round(total / len(components), 3)

        # Identify missing components
        field_names = [
            "dataset", "data_preprocessing", "code", "model_specification",
            "hyperparameters", "training_procedure", "random_seeds",
            "evaluation_metrics", "baselines", "statistical_reporting",
            "hardware_environment", "external_validation", "experimental_protocol",
        ]
        self.missing_components = [
            field_names[i] for i, c in enumerate(components)
            if c in (Availability.NOT_FOUND, Availability.UNAVAILABLE)
        ]
        return self.completeness_score


class ResearchGap(BaseModel):
    """An identified research gap."""
    id: str = Field(default_factory=new_id)
    title: str
    description: str
    gap_type: str = "underexplored"  # underexplored, conflicting, missing, methodological
    gap_dimension: Optional[GapDimension] = None
    evidence: list[str] = []
    supporting_paper_ids: list[str] = []
    missing_dimension: str = ""
    affected_literature: list[str] = []
    confidence: EvidenceConfidence = EvidenceConfidence.MEDIUM
    importance: str = "medium"  # critical, high, medium, low
    novelty_potential: str = "medium"  # high, medium, low
    feasibility: str = "medium"  # high, medium, low
    potential_direction: Optional[str] = None
    why_it_matters: Optional[str] = None


class GapList(BaseModel):
    gaps: list[ResearchGap] = []


class NoveltyAssessment(BaseModel):
    """Novelty analysis of a proposed research idea."""
    id: str = Field(default_factory=new_id)
    proposed_idea: str = ""
    closest_papers: list[str] = []  # paper IDs
    semantic_similarity_scores: dict[str, float] = Field(default_factory=dict)
    methodological_overlap: list[str] = []
    dataset_overlap: list[str] = []
    evaluation_overlap: list[str] = []
    explored_dimensions: list[str] = []
    potentially_unexplored: list[str] = []
    assessment: str = "unclear"  # uses NoveltyLevel values
    novelty_level: NoveltyLevel = NoveltyLevel.INSUFFICIENT_EVIDENCE
    explanation: str = ""
    warnings: list[str] = []
    supporting_literature: list[str] = []


class ExperimentProposal(BaseModel):
    """A proposed experiment design."""
    id: str = Field(default_factory=new_id)
    gap_id: Optional[str] = None
    dead_end_ids: list[str] = []  # dead ends this accounts for
    hypothesis: str
    research_question: str = ""
    research_objective: str
    independent_variables: list[str] = []
    dependent_variables: list[str] = []
    control_variables: list[str] = []
    datasets: list[str] = []
    train_test_split: Optional[str] = None
    experimental_variables: list[str] = []
    baseline_models: list[str] = []
    proposed_method: str = ""
    evaluation_metrics: list[str] = []
    ablation_studies: list[str] = []
    statistical_tests: list[str] = []
    sample_size_guidance: str = ""
    cross_validation_strategy: str = ""
    expected_outcomes: list[str] = []
    failure_criteria: list[str] = []
    success_criteria: list[str] = []
    reproducibility_requirements: list[str] = []
    expected_risks: list[str] = []
    alternative_interpretations: list[str] = []
    addresses_gap: str = ""  # textual trace to gap
    motivated_by_evidence: list[str] = []  # paper_ids
    avoids_dead_ends: list[str] = []  # dead_end_ids


# ─── Red Team ────────────────────────────────────────────

class RedTeamFinding(BaseModel):
    """Individual red team finding with provenance."""
    id: str = Field(default_factory=new_id)
    severity: RedTeamSeverity = RedTeamSeverity.MEDIUM
    finding_type: RedTeamFindingType = RedTeamFindingType.UNSUPPORTED_CLAIM
    description: str
    evidence_refs: list[str] = []  # paper_ids or claim_ids
    affected_claims: list[str] = []  # claim_ids
    recommended_correction: str = ""


class RedTeamResult(BaseModel):
    """Red team analysis result."""
    id: str = Field(default_factory=new_id)
    conclusion_challenged: str = ""
    challenges: list[str] = []
    findings: list[RedTeamFinding] = []
    weak_evidence: list[str] = []
    potential_biases: list[str] = []
    missing_perspectives: list[str] = []
    overgeneralizations: list[str] = []
    final_confidence: EvidenceConfidence = EvidenceConfidence.MEDIUM
    adjudication: str = ""


# ─── Integrity ───────────────────────────────────────────

class IntegrityFinding(BaseModel):
    """Individual integrity check finding."""
    check_name: str
    passed: bool
    details: str = ""
    affected_ids: list[str] = []


class AuditResult(BaseModel):
    """Research integrity audit result."""
    id: str = Field(default_factory=new_id)
    total_claims: int = 0
    claims_with_evidence_links: int = 0
    unsupported_claims: int = 0
    identifiable_source_metadata: int = 0
    citations_total: int = 0
    contradictions_represented: bool = False
    bibliographic_metadata_complete: bool = False
    uncertainty_levels_present: bool = False
    integrity_findings: list[IntegrityFinding] = []
    issues: list[str] = []
    warnings: list[str] = []
    overall_integrity: str = "pending"  # uses IntegrityVerdict values
    verdict: IntegrityVerdict = IntegrityVerdict.PASS


class MissingExperiment(BaseModel):
    """A potentially missing experiment combination."""
    id: str = Field(default_factory=new_id)
    method: str
    dataset: str
    condition: Optional[str] = None
    existing_coverage: list[str] = []  # paper IDs that do adjacent experiments
    explanation: str = ""


class MissingExperimentList(BaseModel):
    experiments: list[MissingExperiment] = []


# ─── Agent Events & Observability ────────────────────────

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
    input_artifact_ids: list[str] = []
    output_artifact_ids: list[str] = []
    retry_count: int = 0


class SearchResult(BaseModel):
    """Result from a search query."""
    query: str
    provider: str
    papers_found: int = 0
    paper_ids: list[str] = []


class RunStats(BaseModel):
    """Research run statistics for observability."""
    research_run_id: str = ""
    total_provider_calls: int = 0
    total_llm_calls: int = 0
    total_tokens_used: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    failed_calls: int = 0
    total_latency_ms: int = 0
    stage_timings: dict[str, int] = Field(default_factory=dict)


# ─── Research Session ────────────────────────────────────

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
    claim_propagations: list[ClaimPropagation] = []
    citation_echoes: list[CitationEchoCluster] = []
    contradictions: list[Contradiction] = []
    consensus: list[ConsensusFinding] = []
    dead_ends: list[DeadEnd] = []
    reproducibility_profiles: dict[str, ReproducibilityProfile] = Field(default_factory=dict)
    gaps: list[ResearchGap] = []
    missing_experiments: list[MissingExperiment] = []
    novelty: Optional[NoveltyAssessment] = None
    experiment: Optional[ExperimentProposal] = None
    red_team: Optional[RedTeamResult] = None
    audit: Optional[AuditResult] = None
    agent_events: list[AgentEvent] = []
    run_stats: Optional[RunStats] = None
    stats: dict[str, Any] = Field(default_factory=dict)
    is_demo: bool = False
    iteration_count: int = 0
    max_iterations: int = 2

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
            "claim_propagations": len(self.claim_propagations),
            "citation_echoes": len(self.citation_echoes),
            "dead_ends": len(self.dead_ends),
            "reproducibility_profiles": len(self.reproducibility_profiles),
        }


# ─── WHY / Explainability ───────────────────────────────

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
    target_type: str  # 'contradiction' | 'consensus' | 'gap' | 'paper' | 'novelty' | 'red_team' | 'dead_end'
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
    year: int | str
    paradigm: str
    title: str
    description: str
    paper_ids: list[str] = []
    key_methods: list[str] = []
    breakthrough_indicator: bool = False


# ─── Research Graph Contract (for future frontend) ──────

class GraphNode(BaseModel):
    """Node in the research knowledge graph."""
    id: str
    node_type: str  # PAPER, CLAIM, EVIDENCE, METHOD, DATASET, GAP, DEAD_END, EXPERIMENT
    label: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """Edge in the research knowledge graph."""
    source_id: str
    target_id: str
    edge_type: str  # SUPPORTS, CONTRADICTS, CITES, DERIVED_FROM, GENERALIZES, etc.
    weight: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResearchGraph(BaseModel):
    """Complete research knowledge graph for frontend visualization."""
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    clusters: dict[str, list[str]] = Field(default_factory=dict)  # cluster_name -> node_ids
