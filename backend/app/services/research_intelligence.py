"""Deterministic research intelligence computations for NEXUS.

This module implements research-specific algorithms that do NOT require LLM calls:
- Citation echo detection
- Evidence strength computation
- Independence weighting
- Reproducibility profiling
- Contradiction candidate generation
- Confidence propagation
- Dead-end detection heuristics
- ClaimLine tracking
- Research graph construction

These are the computational heart of NEXUS — they make it a research system,
not just an LLM wrapper.
"""
import logging
import re
from collections import defaultdict
from typing import Any, Optional

from backend.app.models.research import (
    ResearchSession, Paper, Claim, Evidence, CitationEdge, Contradiction,
    ConsensusFinding, ClaimPropagation, CitationEchoCluster, DeadEnd,
    ReproducibilityProfile, EvidenceStrength, ResearchGap, GraphNode,
    GraphEdge, ResearchGraph, PaperAnalysis, MethodPipeline,
    EvidenceConfidence, ContradictionType, ConsensusStatus, Availability,
    DeadEndStatus, CitationRelation, ClaimPropagationType, GapDimension,
    IntegrityFinding, IntegrityVerdict, AuditResult, RedTeamFinding,
    RedTeamFindingType, RedTeamSeverity,
)

logger = logging.getLogger(__name__)


# ─── Citation Graph Builder ───────────────────────────────

def build_citation_graph(session: ResearchSession) -> list[CitationEdge]:
    """Build the citation relationship graph across session papers.
    
    Combines verified provider reference/citation metadata with deterministic
    textual reference matching. Mark verified vs inferred provenance explicitly.
    """
    edges: list[CitationEdge] = []
    seen_pairs: set[tuple[str, str]] = set()

    def normalize_title(title: str) -> str:
        t = title.lower().strip()
        t = re.sub(r'[^\w\s]', '', t)
        t = re.sub(r'\s+', ' ', t)
        return t

    # Lookup tables
    paper_titles = {normalize_title(p.title): p.id for p in session.papers.values() if p.title}
    paper_dois = {p.doi.lower().strip(): p.id for p in session.papers.values() if p.doi}

    # 1. Inspect each paper for citations
    for source_id, paper in session.papers.items():
        # A) Explicit provider metadata (e.g., sections, references or source_ids)
        if paper.sections:
            ref_section = paper.sections.get("references", "") or paper.sections.get("bibliography", "")
            if ref_section:
                # Check for DOI mentions in references
                for doi_str, target_id in paper_dois.items():
                    if target_id != source_id and (source_id, target_id) not in seen_pairs:
                        if doi_str in ref_section.lower():
                            seen_pairs.add((source_id, target_id))
                            edges.append(CitationEdge(
                                source_paper_id=source_id,
                                target_paper_id=target_id,
                                relation=CitationRelation.CITES,
                                context=f"Verified DOI reference ({doi_str}) in references section",
                                is_inferred=False,
                            ))

        # B) Deterministic textual title matching across abstracts and full-text sections
        searchable_text = (paper.abstract or "").lower()
        if paper.sections:
            searchable_text += " " + " ".join(paper.sections.values()).lower()

        for norm_title, target_id in paper_titles.items():
            if target_id != source_id and len(norm_title) > 12 and (source_id, target_id) not in seen_pairs:
                if norm_title in searchable_text:
                    seen_pairs.add((source_id, target_id))
                    edges.append(CitationEdge(
                        source_paper_id=source_id,
                        target_paper_id=target_id,
                        relation=CitationRelation.CITES,
                        context=f"Inferred citation via title mention '{norm_title[:40]}...'",
                        is_inferred=True,
                    ))

    return edges


# ─── Contradiction Candidate Ranking ─────────────────────

def generate_contradiction_candidates(
    claims: list[Claim],
    papers: dict[str, 'Paper'],
    max_pairs: int = 12,
) -> list[tuple[Claim, Claim]]:
    """Generate ranked contradiction candidate pairs using deterministic heuristics.

    Scores each cross-paper claim pair by:
    - Shared metric/topic overlap (higher = more likely contradiction)
    - Opposing signal words (e.g. "increases" vs "decreases")
    - Evidence strength differential (high-confidence disagreements matter most)
    - Shared condition overlap (same conditions → more meaningful conflict)
    
    Returns the top-N highest-priority pairs for LLM adjudication.
    """
    if len(claims) < 2:
        return []

    OPPOSING_SIGNALS = [
        ("increase", "decrease"), ("improve", "degrade"), ("better", "worse"),
        ("higher", "lower"), ("outperform", "underperform"), ("gain", "loss"),
        ("positive", "negative"), ("efficient", "inefficient"), ("fast", "slow"),
        ("accurate", "inaccurate"), ("robust", "fragile"), ("enhance", "diminish"),
        ("significant", "insignificant"),
    ]

    def _signal_opposition(text_a: str, text_b: str) -> float:
        """Check if claims contain opposing directional signals."""
        a_lower, b_lower = text_a.lower(), text_b.lower()
        for pos, neg in OPPOSING_SIGNALS:
            if (pos in a_lower and neg in b_lower) or (neg in a_lower and pos in b_lower):
                return 1.0
        return 0.0

    def _metric_overlap(a: Claim, b: Claim) -> float:
        """Score metric field alignment."""
        if a.metric and b.metric:
            ma, mb = a.metric.lower().strip(), b.metric.lower().strip()
            if ma == mb:
                return 1.0
            # Partial overlap (shared words)
            a_words = set(ma.split())
            b_words = set(mb.split())
            if a_words & b_words:
                return 0.5
        return 0.0

    def _condition_overlap(a: Claim, b: Claim) -> float:
        """Claims with shared conditions are more meaningful to compare."""
        if not a.conditions or not b.conditions:
            return 0.0
        a_set = set(c.lower().strip() for c in a.conditions)
        b_set = set(c.lower().strip() for c in b.conditions)
        if not a_set or not b_set:
            return 0.0
        return len(a_set & b_set) / max(len(a_set | b_set), 1)

    def _evidence_strength_score(claim: Claim) -> float:
        """Higher evidence strength → higher priority for contradiction checking."""
        if claim.strength:
            return claim.strength.composite_score
        conf_map = {"high": 0.9, "medium": 0.6, "low": 0.3, "uncertain": 0.2, "insufficient": 0.1}
        return conf_map.get(claim.confidence.value, 0.5)

    # Generate all cross-paper pairs with scores
    scored_pairs: list[tuple[float, Claim, Claim]] = []
    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):
            a, b = claims[i], claims[j]
            if a.paper_id == b.paper_id:
                continue
            
            score = 0.0
            score += 3.0 * _signal_opposition(a.statement, b.statement)
            score += 2.0 * _metric_overlap(a, b)
            score += 1.5 * _condition_overlap(a, b)
            # High-evidence disagreements are more important
            avg_strength = (_evidence_strength_score(a) + _evidence_strength_score(b)) / 2
            score += 1.0 * avg_strength
            # Boost if same metric but different values
            if a.evidence_value and b.evidence_value and a.metric and b.metric:
                if a.metric.lower() == b.metric.lower() and a.evidence_value != b.evidence_value:
                    score += 2.0

            scored_pairs.append((score, a, b))

    # Sort by score descending, take top-N
    scored_pairs.sort(key=lambda x: x[0], reverse=True)
    return [(a, b) for _, a, b in scored_pairs[:max_pairs]]


# ─── Red Team Evidence Ranking ────────────────────────────

def rank_red_team_evidence(session: ResearchSession, max_items: int = 15) -> list:
    """Select evidence for Red Team review based on risk signals (deterministic).
    
    Prioritizes:
    1. Evidence backing contradicted or contested claims
    2. Evidence from papers with low reproducibility scores
    3. Evidence from claims with citation echo dependencies
    4. Evidence with low directness or scope_alignment
    """
    evidence_scores: list[tuple[float, 'Evidence']] = []
    
    # Pre-compute risk indices
    contradicted_claim_ids = set()
    for c in session.contradictions:
        contradicted_claim_ids.add(c.claim_a_id)
        contradicted_claim_ids.add(c.claim_b_id)
    
    echo_paper_ids = set()
    for echo in session.citation_echoes:
        echo_paper_ids.update(echo.echo_paper_ids)
    
    low_repro_paper_ids = set()
    for pid, prof in session.reproducibility_profiles.items():
        if prof.completeness_score < 0.5:
            low_repro_paper_ids.add(pid)

    for ev in session.evidence:
        score = 0.0
        # Risk signal 1: backs a contradicted claim
        if ev.claim_id in contradicted_claim_ids:
            score += 3.0
        # Risk signal 2: from low-reproducibility paper
        if ev.paper_id in low_repro_paper_ids:
            score += 2.0
        # Risk signal 3: from echo chamber paper
        if ev.paper_id in echo_paper_ids:
            score += 1.5
        # Risk signal 4: low evidence strength
        claim = next((c for c in session.claims if c.id == ev.claim_id), None)
        if claim and claim.strength:
            if claim.strength.directness < 0.4:
                score += 1.0
            if claim.strength.scope_alignment < 0.4:
                score += 1.0
        # Baseline score for all evidence
        score += 0.1
        evidence_scores.append((score, ev))
    
    evidence_scores.sort(key=lambda x: x[0], reverse=True)
    return [ev for _, ev in evidence_scores[:max_items]]


# ─── Citation Echo Detection ─────────────────────────────

def detect_citation_echoes(session: ResearchSession) -> list[CitationEchoCluster]:
    """Detect citation echo chambers where apparent consensus traces to few sources.

    This is deterministic — no LLM needed.
    """
    echoes = []
    if not session.citations or not session.claims:
        return echoes

    # Build adjacency: paper_id -> set of paper_ids it cites
    cites_graph: dict[str, set[str]] = defaultdict(set)
    cited_by: dict[str, set[str]] = defaultdict(set)
    for edge in session.citations:
        cites_graph[edge.source_paper_id].add(edge.target_paper_id)
        cited_by[edge.target_paper_id].add(edge.source_paper_id)

    # For each claim, find the originating paper and all papers that support it
    claim_papers: dict[str, list[str]] = defaultdict(list)
    for claim in session.claims:
        claim_papers[claim.statement].append(claim.paper_id)

    # Group similar claims by normalized statement
    normalized_claims: dict[str, list[Claim]] = defaultdict(list)
    for claim in session.claims:
        norm = _normalize_claim(claim.statement)
        normalized_claims[norm].append(claim)

    for norm_stmt, claims in normalized_claims.items():
        if len(claims) < 2:
            continue

        paper_ids = list(set(c.paper_id for c in claims))
        if len(paper_ids) < 2:
            continue

        # Find the earliest/originating paper
        originating_id = _find_originating_paper(paper_ids, cites_graph, session.papers)
        if not originating_id:
            continue

        # Trace dependency chains
        echo_papers = []
        independent_papers = []
        for pid in paper_ids:
            if pid == originating_id:
                continue
            if _traces_to_source(pid, originating_id, cites_graph, max_depth=4):
                echo_papers.append(pid)
            else:
                independent_papers.append(pid)

        if echo_papers:
            depth = _max_chain_depth(originating_id, echo_papers, cites_graph)
            total = len(paper_ids)
            independent = len(independent_papers) + 1  # +1 for originating
            independence_weight = independent / total if total > 0 else 1.0

            originating_paper = session.papers.get(originating_id)
            echoes.append(CitationEchoCluster(
                claim_statement=claims[0].statement,
                originating_paper_id=originating_id,
                originating_paper_title=originating_paper.title if originating_paper else "",
                echo_paper_ids=echo_papers,
                total_support_count=total,
                independent_support_count=independent,
                citation_dependency_depth=depth,
                echo_chain=[originating_id] + echo_papers,
                independence_weight=round(independence_weight, 3),
                explanation=f"Of {total} papers supporting this claim, {len(echo_papers)} "
                           f"trace citation dependency to {originating_paper.title if originating_paper else originating_id}. "
                           f"Only {independent} source(s) provide independent support."
            ))

    return echoes


def _normalize_claim(statement: str) -> str:
    """Normalize claim for similarity comparison."""
    s = statement.lower().strip()
    s = re.sub(r'[^a-z0-9\s]', '', s)
    s = re.sub(r'\s+', ' ', s)
    # Remove common filler
    for word in ['the', 'a', 'an', 'is', 'are', 'was', 'were', 'for', 'of', 'in', 'on', 'to']:
        s = re.sub(rf'\b{word}\b', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def _find_originating_paper(paper_ids: list[str], cites_graph: dict[str, set[str]],
                             papers: dict[str, Paper]) -> Optional[str]:
    """Find the earliest/most-cited paper as likely originator."""
    # Paper that is cited by most others in the set
    cite_counts = defaultdict(int)
    for pid in paper_ids:
        for cited in cites_graph.get(pid, set()):
            if cited in paper_ids:
                cite_counts[cited] += 1

    if cite_counts:
        return max(cite_counts, key=cite_counts.get)

    # Fallback: earliest by year
    valid = [(pid, papers[pid].year or 9999) for pid in paper_ids if pid in papers]
    if valid:
        return min(valid, key=lambda x: x[1])[0]
    return paper_ids[0] if paper_ids else None


def _traces_to_source(paper_id: str, source_id: str, cites_graph: dict[str, set[str]],
                       max_depth: int = 4) -> bool:
    """Check if paper_id transitively cites source_id."""
    visited = set()
    queue = [paper_id]
    depth = 0
    while queue and depth < max_depth:
        next_queue = []
        for pid in queue:
            if pid in visited:
                continue
            visited.add(pid)
            for cited in cites_graph.get(pid, set()):
                if cited == source_id:
                    return True
                next_queue.append(cited)
        queue = next_queue
        depth += 1
    return False


def _max_chain_depth(originating_id: str, echo_papers: list[str],
                      cites_graph: dict[str, set[str]]) -> int:
    """Find maximum citation chain depth from originating paper."""
    max_depth = 0
    for pid in echo_papers:
        depth = _find_depth(pid, originating_id, cites_graph, set(), 0)
        max_depth = max(max_depth, depth)
    return max_depth


def _find_depth(current: str, target: str, cites_graph: dict[str, set[str]],
                 visited: set, depth: int) -> int:
    if depth > 5 or current in visited:
        return 0
    visited.add(current)
    for cited in cites_graph.get(current, set()):
        if cited == target:
            return depth + 1
        result = _find_depth(cited, target, cites_graph, visited, depth + 1)
        if result > 0:
            return result
    return 0


# ─── Reproducibility Profiling ───────────────────────────

def compute_reproducibility_profile(paper: Paper, analysis: Optional[PaperAnalysis]) -> ReproducibilityProfile:
    """Deterministically compute reproducibility profile from paper metadata and analysis."""
    profile = ReproducibilityProfile(paper_id=paper.id)

    if analysis:
        profile.code_available = analysis.code_availability
        profile.dataset_available = analysis.dataset_availability

        # Check method documentation
        if analysis.methods:
            method = analysis.methods[0]
            profile.model_specification_documented = (
                Availability.AVAILABLE if method.model_details else Availability.PARTIAL if method.model_architecture else Availability.UNKNOWN
            )
            profile.hyperparameters_documented = (
                Availability.AVAILABLE if method.optimizer and method.loss_function else
                Availability.PARTIAL if method.optimizer or method.loss_function else Availability.UNKNOWN
            )
            profile.training_procedure_documented = (
                Availability.AVAILABLE if method.training_procedure else Availability.UNKNOWN
            )
            profile.evaluation_metrics_defined = (
                Availability.AVAILABLE if method.metrics else Availability.UNKNOWN
            )
            profile.baselines_reproducible = (
                Availability.AVAILABLE if len(method.baselines) >= 2 else
                Availability.PARTIAL if method.baselines else Availability.UNKNOWN
            )
            profile.experimental_protocol_documented = (
                Availability.AVAILABLE if method.evaluation_protocol else Availability.UNKNOWN
            )
            profile.data_preprocessing_documented = (
                Availability.AVAILABLE if method.preprocessing else Availability.UNKNOWN
            )

        # Infer from reproducibility_indicators if present
        indicators = analysis.reproducibility_indicators
        if indicators.get("random_seeds"):
            profile.random_seeds_reported = Availability.AVAILABLE
        if indicators.get("hardware"):
            profile.hardware_environment_documented = Availability.AVAILABLE
        if indicators.get("statistical_tests"):
            profile.statistical_reporting = Availability.AVAILABLE

    # Compute completeness
    profile.compute_completeness()

    # Generate structured reproducibility blockers
    from backend.app.models.research import ReproducibilityBlocker

    if profile.code_available in (Availability.NOT_FOUND, Availability.UNAVAILABLE):
        profile.blockers.append(ReproducibilityBlocker(
            category="CODE_UNAVAILABLE",
            severity="critical",
            affected_component="implementation",
            evidence="No source code or reference implementation found",
            recommended_remediation="Request code from authors or re-implement from paper description"
        ))
        profile.risk_factors.append("No code available — implementation details unverifiable")

    if profile.random_seeds_reported in (Availability.UNKNOWN, Availability.NOT_FOUND):
        profile.blockers.append(ReproducibilityBlocker(
            category="MISSING_RANDOM_SEED",
            severity="high",
            affected_component="training",
            evidence="Random seeds not reported in paper or supplementary material",
            recommended_remediation="Run with ≥3 seeds and report mean ± std"
        ))
        profile.risk_factors.append("Random seeds not reported — results may not be exactly reproducible")

    if profile.dataset_available in (Availability.NOT_FOUND, Availability.UNAVAILABLE):
        profile.blockers.append(ReproducibilityBlocker(
            category="DATASET_UNAVAILABLE",
            severity="critical",
            affected_component="data",
            evidence="Training/evaluation data not publicly accessible",
            recommended_remediation="Use comparable public benchmarks or request data access"
        ))

    if profile.data_preprocessing_documented in (Availability.NOT_FOUND, Availability.UNKNOWN):
        profile.blockers.append(ReproducibilityBlocker(
            category="MISSING_PREPROCESSING_SPEC",
            severity="medium",
            affected_component="data pipeline",
            evidence="Data preprocessing steps not documented",
            recommended_remediation="Document all preprocessing including normalization, tokenization, and splitting"
        ))

    if profile.hyperparameters_documented in (Availability.NOT_FOUND, Availability.UNKNOWN):
        profile.blockers.append(ReproducibilityBlocker(
            category="MISSING_HYPERPARAMETERS",
            severity="high",
            affected_component="model configuration",
            evidence="Hyperparameters not fully reported",
            recommended_remediation="Provide complete hyperparameter table in paper or supplementary"
        ))

    if profile.statistical_reporting in (Availability.UNKNOWN, Availability.NOT_FOUND):
        profile.blockers.append(ReproducibilityBlocker(
            category="MISSING_STATISTICAL_TESTS",
            severity="medium",
            affected_component="evaluation",
            evidence="No statistical significance tests (p-values, confidence intervals) reported",
            recommended_remediation="Report statistical significance with appropriate tests (e.g., paired t-test, bootstrap CI)"
        ))
        profile.risk_factors.append("No statistical significance tests reported")

    if profile.hardware_environment_documented in (Availability.UNKNOWN, Availability.NOT_FOUND):
        profile.blockers.append(ReproducibilityBlocker(
            category="MISSING_HARDWARE_SPEC",
            severity="low",
            affected_component="environment",
            evidence="Hardware/software environment not documented",
            recommended_remediation="Document GPU model, driver version, framework version, and OS"
        ))
        profile.risk_factors.append("Hardware/environment not documented — performance may vary")

    if profile.external_validation in (Availability.UNKNOWN, Availability.NOT_FOUND):
        profile.risk_factors.append("No external validation — results only verified on original setup")

    profile.explanation = (
        f"Reproducibility completeness: {profile.completeness_score:.0%}. "
        f"{len(profile.missing_components)} components missing, "
        f"{len(profile.blockers)} blockers identified ({sum(1 for b in profile.blockers if b.severity == 'critical')} critical), "
        f"{len(profile.risk_factors)} risk factors."
    )

    return profile




# ─── Dead-End Detection ─────────────────────────────────

def detect_dead_ends(session: ResearchSession) -> list[DeadEnd]:
    """Detect research dead ends from analysis data.

    Identifies approaches that:
    - Repeatedly failed
    - Failed under specific conditions
    - Were superseded
    - Had consistently poor results
    """
    dead_ends = []

    # Collect all methods and their outcomes
    method_outcomes: dict[str, list[dict]] = defaultdict(list)
    for paper_id, analysis in session.analyses.items():
        paper = session.papers.get(paper_id)
        if not paper:
            continue

        for method in analysis.methods:
            arch = method.model_architecture
            if not arch:
                continue
            outcome = {
                "paper_id": paper_id,
                "paper_title": paper.title,
                "dataset": method.dataset,
                "baselines": method.baselines,
                "limitations": analysis.limitations,
            }
            method_outcomes[arch.lower()].append(outcome)

    # Check for methods that appear as baselines but are consistently beaten
    baseline_losses: dict[str, list[str]] = defaultdict(list)
    for paper_id, analysis in session.analyses.items():
        for method in analysis.methods:
            for baseline in method.baselines:
                baseline_losses[baseline.lower()].append(paper_id)

    # Methods that appear more often as beaten baselines than as proposed methods
    for method_name, losing_papers in baseline_losses.items():
        if len(losing_papers) >= 2:
            winning_count = len(method_outcomes.get(method_name, []))
            if winning_count == 0 or len(losing_papers) > winning_count * 2:
                # Collect failure conditions from limitations
                failure_conditions = []
                for paper_id in losing_papers:
                    paper = session.papers.get(paper_id)
                    analysis = session.analyses.get(paper_id)
                    if analysis:
                        for lim in analysis.limitations:
                            if method_name in lim.lower():
                                failure_conditions.append(lim)

                # Collect dataset/metric context from losing papers
                datasets_seen = set()
                metrics_seen = set()
                for pid in losing_papers:
                    a = session.analyses.get(pid)
                    if a:
                        for m in a.methods:
                            if m.dataset:
                                datasets_seen.add(m.dataset)
                            metrics_seen.update(m.metrics)

                status = DeadEndStatus.SUPERSEDED if len(losing_papers) >= 3 else DeadEndStatus.LIMITED
                if failure_conditions:
                    status = DeadEndStatus.CONDITIONAL_FAILURE
                if len(losing_papers) >= 3 and not failure_conditions:
                    status = DeadEndStatus.REPEATEDLY_UNDERPERFORMING

                dead_ends.append(DeadEnd(
                    approach=method_name.upper(),
                    description=f"{method_name.upper()} consistently outperformed by newer methods "
                               f"across {len(losing_papers)} studies",
                    supporting_papers=losing_papers,
                    failure_evidence=[f"Used as baseline and outperformed in {len(losing_papers)} papers"],
                    failure_conditions=failure_conditions[:5],
                    task="general" if not datasets_seen else f"evaluation on {', '.join(sorted(datasets_seen)[:3])}",
                    dataset=", ".join(sorted(datasets_seen)[:3]) if datasets_seen else "",
                    metric=", ".join(sorted(metrics_seen)[:3]) if metrics_seen else "",
                    failure_reason="consistently_outperformed" if not failure_conditions else "conditional_limitation",
                    attempt_count=len(losing_papers),
                    status=status,
                    confidence=EvidenceConfidence.HIGH if len(losing_papers) >= 3 else EvidenceConfidence.MEDIUM,
                ))

    # Check claims for explicit failure conditions
    for claim in session.claims:
        stmt_lower = claim.statement.lower()
        failure_keywords = ["fail", "not justified", "underperform", "degrade", "worse",
                           "not suitable", "insufficient", "limited", "not effective"]
        if any(kw in stmt_lower for kw in failure_keywords):
            # This claim describes a failure or limitation
            paper = session.papers.get(claim.paper_id)
            existing = next((d for d in dead_ends if _claims_overlap(d.approach.lower(), stmt_lower)), None)
            if existing:
                if claim.paper_id not in existing.supporting_papers:
                    existing.supporting_papers.append(claim.paper_id)
                    existing.attempt_count += 1
                    existing.failure_evidence.append(claim.statement)
            else:
                # Determine failure reason from keywords
                failure_reason = "general_limitation"
                if "fail" in stmt_lower:
                    failure_reason = "explicit_failure"
                elif "not suitable" in stmt_lower or "not effective" in stmt_lower:
                    failure_reason = "unsuitability"
                elif "degrade" in stmt_lower or "worse" in stmt_lower:
                    failure_reason = "performance_degradation"
                elif "underperform" in stmt_lower:
                    failure_reason = "underperformance"
                elif "insufficient" in stmt_lower or "limited" in stmt_lower:
                    failure_reason = "insufficient_capability"

                # Use conditional status if conditions present
                status = DeadEndStatus.LIMITED
                if claim.conditions:
                    status = DeadEndStatus.WEAK_UNDER_SPECIFIC_CONDITIONS

                dead_ends.append(DeadEnd(
                    approach=_extract_approach_name(claim.statement),
                    description=claim.statement,
                    supporting_papers=[claim.paper_id],
                    failure_evidence=[claim.statement],
                    failure_conditions=claim.conditions,
                    task=claim.metric or "",
                    dataset="",
                    metric=claim.metric or "",
                    failure_reason=failure_reason,
                    attempt_count=1,
                    status=status,
                    confidence=claim.confidence,
                    success_conditions_if_any=[],
                ))

    return dead_ends


def _claims_overlap(approach: str, statement: str) -> bool:
    """Check if a dead-end approach name appears in a claim statement."""
    return approach in statement


def _extract_approach_name(statement: str) -> str:
    """Extract the approach/method name from a failure claim."""
    # Look for known method names
    known_methods = ["GNN", "GAT", "GCN", "LSTM", "GRU", "CNN", "Transformer",
                     "MLP", "RNN", "BERT", "GPT", "SVM", "Random Forest"]
    for method in known_methods:
        if method.lower() in statement.lower():
            return method
    # Fallback: use first few significant words
    words = [w for w in statement.split()[:5] if len(w) > 3]
    return " ".join(words[:3]) if words else "Unknown approach"


# ─── ClaimLine Tracking ──────────────────────────────────

def build_claim_propagations(session: ResearchSession) -> list[ClaimPropagation]:
    """Track how claims propagate and transform across papers.

    Detects: preservation, weakening, strengthening, generalization,
    context shifting, unsupported extension.
    """
    propagations = []
    if len(session.claims) < 2 or not session.citations:
        return propagations

    # Build citation lookup
    cites: dict[str, set[str]] = defaultdict(set)
    for edge in session.citations:
        cites[edge.source_paper_id].add(edge.target_paper_id)

    # For each claim, check if a citing paper has a related claim
    claims_by_paper: dict[str, list[Claim]] = defaultdict(list)
    for claim in session.claims:
        claims_by_paper[claim.paper_id].append(claim)

    for edge in session.citations:
        source_claims = claims_by_paper.get(edge.source_paper_id, [])
        target_claims = claims_by_paper.get(edge.target_paper_id, [])

        for s_claim in source_claims:
            for t_claim in target_claims:
                # Check if claims are related
                similarity = _claim_similarity(s_claim.statement, t_claim.statement)
                if similarity < 0.3:
                    continue

                # Determine propagation type
                prop_type = _classify_propagation(t_claim, s_claim)

                propagations.append(ClaimPropagation(
                    source_claim_id=t_claim.id,  # original claim
                    derived_claim_id=s_claim.id,  # citing paper's version
                    source_paper_id=edge.target_paper_id,
                    derived_paper_id=edge.source_paper_id,
                    relationship_type=prop_type,
                    source_conditions=t_claim.conditions,
                    derived_conditions=s_claim.conditions,
                    evidence_strength=s_claim.confidence,
                    scope_change=_describe_scope_change(t_claim, s_claim),
                    confidence=EvidenceConfidence.MEDIUM,
                    explanation=_explain_propagation(t_claim, s_claim, prop_type),
                ))

    return propagations


def _claim_similarity(s1: str, s2: str) -> float:
    """Simple word-overlap similarity between two claims."""
    w1 = set(re.sub(r'[^a-z0-9\s]', '', s1.lower()).split())
    w2 = set(re.sub(r'[^a-z0-9\s]', '', s2.lower()).split())
    # Remove stopwords
    stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'for', 'of', 'in', 'on', 'to', 'and', 'or', 'but'}
    w1 -= stopwords
    w2 -= stopwords
    if not w1 or not w2:
        return 0.0
    intersection = w1 & w2
    union = w1 | w2
    return len(intersection) / len(union) if union else 0.0


def _classify_propagation(original: Claim, derived: Claim) -> ClaimPropagationType:
    """Classify how a claim was transformed during propagation."""
    orig_conds = set(c.lower() for c in original.conditions)
    deriv_conds = set(c.lower() for c in derived.conditions)

    # Check for scope broadening (generalization)
    if orig_conds and not deriv_conds:
        return ClaimPropagationType.GENERALIZED
    if orig_conds and deriv_conds and len(deriv_conds) < len(orig_conds):
        removed_conditions = orig_conds - deriv_conds
        if removed_conditions:
            return ClaimPropagationType.GENERALIZED

    # Check for scope narrowing (specialization)
    if deriv_conds and len(deriv_conds) > len(orig_conds):
        return ClaimPropagationType.SPECIALIZED

    # Check for context shift
    if orig_conds and deriv_conds and not (orig_conds & deriv_conds):
        return ClaimPropagationType.CONTEXT_SHIFTED

    # Check for contradiction
    orig_lower = original.statement.lower()
    deriv_lower = derived.statement.lower()
    negation_words = ["not", "no", "never", "fails", "worse", "underperform"]
    orig_neg = any(w in orig_lower for w in negation_words)
    deriv_neg = any(w in deriv_lower for w in negation_words)
    if orig_neg != deriv_neg:
        return ClaimPropagationType.CONTRADICTED

    # Check for weakening/strengthening
    strength_words = {"significantly", "substantially", "strongly", "clearly", "definitively"}
    hedging_words = {"may", "might", "could", "suggests", "partially", "somewhat", "limited"}
    orig_strong = any(w in orig_lower for w in strength_words)
    deriv_strong = any(w in deriv_lower for w in strength_words)
    orig_hedge = any(w in orig_lower for w in hedging_words)
    deriv_hedge = any(w in deriv_lower for w in hedging_words)

    if orig_strong and deriv_hedge:
        return ClaimPropagationType.WEAKENED
    if orig_hedge and deriv_strong:
        return ClaimPropagationType.STRENGTHENED

    return ClaimPropagationType.PRESERVED


def _describe_scope_change(original: Claim, derived: Claim) -> str:
    """Describe how the scope changed between original and derived claim."""
    orig_conds = set(c.lower() for c in original.conditions)
    deriv_conds = set(c.lower() for c in derived.conditions)

    added = deriv_conds - orig_conds
    removed = orig_conds - deriv_conds

    parts = []
    if removed:
        parts.append(f"Dropped conditions: {', '.join(removed)}")
    if added:
        parts.append(f"Added conditions: {', '.join(added)}")
    if not parts:
        parts.append("No scope change detected")
    return "; ".join(parts)


def _explain_propagation(original: Claim, derived: Claim, prop_type: ClaimPropagationType) -> str:
    """Generate explanation for claim propagation."""
    type_descriptions = {
        ClaimPropagationType.PRESERVED: "Claim preserved with consistent scope and conditions",
        ClaimPropagationType.WEAKENED: "Claim weakened — derived version uses more hedging language",
        ClaimPropagationType.STRENGTHENED: "Claim strengthened — derived version makes stronger assertion",
        ClaimPropagationType.GENERALIZED: "Claim generalized — conditions were dropped, broadening scope",
        ClaimPropagationType.SPECIALIZED: "Claim specialized — additional conditions narrow the scope",
        ClaimPropagationType.CONTEXT_SHIFTED: "Context shifted — claim applied to different conditions",
        ClaimPropagationType.CONTRADICTED: "Claim contradicted — derived version opposes original",
        ClaimPropagationType.UNSUPPORTED_EXTENSION: "Unsupported extension — derived claim extends beyond evidence",
    }
    return type_descriptions.get(prop_type, "Unknown propagation type")


# ─── Consensus Independence Weighting ────────────────────

def compute_consensus_independence(finding: ConsensusFinding, session: ResearchSession) -> ConsensusFinding:
    """Adjust consensus confidence based on evidence independence.

    Ten papers all citing the same source ≠ ten independent confirmations.
    """
    if not finding.supporting_paper_ids or len(finding.supporting_paper_ids) < 2:
        finding.independent_support_count = len(finding.supporting_paper_ids)
        finding.independence_weight = 1.0
        return finding

    # Check citation dependencies among supporting papers
    cites: dict[str, set[str]] = defaultdict(set)
    for edge in session.citations:
        cites[edge.source_paper_id].add(edge.target_paper_id)

    supporting = set(finding.supporting_paper_ids)
    independent = set()
    dependent = set()

    for pid in supporting:
        # A paper is dependent if it cites another supporting paper
        cited_supporters = cites.get(pid, set()) & supporting
        if not cited_supporters:
            independent.add(pid)
        else:
            dependent.add(pid)

    # Papers that cite no other supporting papers are independent
    if not independent:
        # All papers cite each other — at least the earliest is independent
        earliest = min(supporting,
                       key=lambda p: session.papers.get(p, Paper(title="")).year or 9999)
        independent.add(earliest)

    finding.independent_support_count = len(independent)
    finding.independence_weight = round(len(independent) / len(supporting), 3) if supporting else 1.0
    finding.evidence_quality_weighted = True

    # Downgrade confidence if independence is low
    if finding.independence_weight < 0.4 and finding.confidence == EvidenceConfidence.HIGH:
        finding.confidence = EvidenceConfidence.MEDIUM
        finding.explanation += (
            f" [Note: Independence weight {finding.independence_weight:.0%} — "
            f"only {len(independent)} of {len(supporting)} supporting papers are "
            f"citation-independent. Confidence downgraded.]"
        )

    return finding


# ─── Evidence Strength Computation ───────────────────────

def compute_evidence_strength(claim: Claim, evidence: list[Evidence],
                                paper: Paper, session: ResearchSession) -> EvidenceStrength:
    """Compute multi-dimensional evidence strength deterministically."""
    strength = EvidenceStrength()

    # Directness
    matching_evidence = [e for e in evidence if e.claim_id == claim.id]
    if matching_evidence:
        has_quantitative = any(e.quantitative_value for e in matching_evidence)
        strength.directness = 0.9 if has_quantitative else 0.6
    else:
        strength.directness = 0.2

    # Source quality (based on citation count and venue)
    if paper.citation_count and paper.citation_count > 50:
        strength.source_quality = 0.8
    elif paper.citation_count and paper.citation_count > 10:
        strength.source_quality = 0.6
    else:
        strength.source_quality = 0.4
    if paper.venue and any(top in paper.venue.lower() for top in
                           ["nature", "science", "ieee trans", "acm", "icml", "neurips", "iclr"]):
        strength.source_quality = min(1.0, strength.source_quality + 0.2)

    # Methodological rigor
    analysis = session.analyses.get(paper.id)
    if analysis and analysis.methods:
        method = analysis.methods[0]
        rigor_score = 0.3
        if method.baselines and len(method.baselines) >= 2:
            rigor_score += 0.2
        if method.evaluation_protocol:
            rigor_score += 0.2
        if "cross-validation" in (method.evaluation_protocol or "").lower():
            rigor_score += 0.1
        if method.metrics and len(method.metrics) >= 2:
            rigor_score += 0.1
        strength.methodological_rigor = min(1.0, rigor_score)

    # Reproducibility
    repro = session.reproducibility_profiles.get(paper.id)
    if repro:
        strength.reproducibility = repro.completeness_score
    elif analysis:
        if analysis.code_availability == Availability.AVAILABLE:
            strength.reproducibility = 0.7
        elif analysis.code_availability == Availability.NOT_FOUND:
            strength.reproducibility = 0.3
        else:
            strength.reproducibility = 0.4

    # Cross-study consistency
    related_claims = [c for c in session.claims
                      if c.paper_id != paper.id and _claim_similarity(c.statement, claim.statement) > 0.4]
    agreeing = sum(1 for c in related_claims if c.confidence in (EvidenceConfidence.HIGH, EvidenceConfidence.MEDIUM))
    if related_claims:
        strength.cross_study_consistency = min(1.0, agreeing / len(related_claims))

    # Scope alignment
    if claim.conditions:
        strength.scope_alignment = 0.7 if len(claim.conditions) >= 2 else 0.5
    else:
        strength.scope_alignment = 0.3  # No conditions = broad/vague scope

    # Overall assessment
    composite = strength.composite_score
    if composite >= 0.7:
        strength.overall_assessment = EvidenceConfidence.HIGH
    elif composite >= 0.5:
        strength.overall_assessment = EvidenceConfidence.MEDIUM
    elif composite >= 0.3:
        strength.overall_assessment = EvidenceConfidence.LOW
    else:
        strength.overall_assessment = EvidenceConfidence.UNCERTAIN

    strength.rationale = (
        f"Composite score: {composite:.2f}. "
        f"Directness: {strength.directness:.2f}, "
        f"Source quality: {strength.source_quality:.2f}, "
        f"Rigor: {strength.methodological_rigor:.2f}, "
        f"Reproducibility: {strength.reproducibility:.2f}"
    )

    return strength


# ─── Integrity Audit (Deterministic) ─────────────────────

def run_deterministic_audit(session: ResearchSession) -> AuditResult:
    """Run deterministic integrity checks — no LLM needed."""
    findings = []
    issues = []
    warnings = []

    total_claims = len(session.claims)
    claims_with_evidence = sum(1 for c in session.claims
                               if any(e.claim_id == c.id for e in session.evidence))
    unsupported = total_claims - claims_with_evidence

    # Check 1: Every major claim has evidence
    if unsupported > 0:
        findings.append(IntegrityFinding(
            check_name="claims_have_evidence",
            passed=unsupported <= 2,
            details=f"{unsupported} of {total_claims} claims lack direct evidence linkage",
            affected_ids=[c.id for c in session.claims
                         if not any(e.claim_id == c.id for e in session.evidence)]
        ))
        if unsupported > 2:
            issues.append(f"{unsupported} claims lack direct evidence linkage")
        else:
            warnings.append(f"{unsupported} claims lack direct evidence (minor)")

    # Check 2: Papers have verifiable metadata
    verified_papers = sum(1 for p in session.papers.values()
                          if p.doi or (p.source_provider and p.source_provider not in ["upload", "demo_inferred"]))
    findings.append(IntegrityFinding(
        check_name="paper_metadata_verifiable",
        passed=verified_papers >= len(session.papers) * 0.8,
        details=f"{verified_papers}/{len(session.papers)} papers have verifiable metadata"
    ))

    # Check 3: Bibliography completeness
    bib_validated = all(
        p.title and p.authors and (p.year or p.venue or p.doi)
        for p in session.papers.values()
    )
    findings.append(IntegrityFinding(
        check_name="bibliography_complete",
        passed=bib_validated,
        details="All papers have title, authors, and date/venue/DOI" if bib_validated
                else "Some papers missing basic bibliographic metadata"
    ))

    # Check 4: Contradictions represented
    if session.contradictions:
        findings.append(IntegrityFinding(
            check_name="contradictions_represented",
            passed=True,
            details=f"{len(session.contradictions)} contradictions identified and documented"
        ))
    else:
        warnings.append("No contradictions detected — may indicate insufficient cross-paper analysis")

    # Check 5: Uncertainty levels present
    has_uncertainty = any(c.confidence for c in session.claims)
    findings.append(IntegrityFinding(
        check_name="uncertainty_levels",
        passed=has_uncertainty,
        details="Uncertainty/confidence levels present on claims" if has_uncertainty
                else "No uncertainty levels assigned to claims"
    ))

    # Check 6: No downstream conclusion exceeds source scope
    scope_violations = []
    for claim in session.claims:
        if claim.status == "invalidated":
            scope_violations.append(claim.id)
    if scope_violations:
        issues.append(f"{len(scope_violations)} claims have been invalidated by downstream analysis")
        findings.append(IntegrityFinding(
            check_name="scope_integrity",
            passed=False,
            details=f"{len(scope_violations)} claims exceed source scope",
            affected_ids=scope_violations
        ))

    # Check 7: Citation echo warnings
    if session.citation_echoes:
        for echo in session.citation_echoes:
            if echo.independence_weight < 0.5:
                warnings.append(
                    f"Citation echo detected: '{echo.claim_statement[:60]}...' — "
                    f"only {echo.independent_support_count}/{echo.total_support_count} independent sources"
                )

    # Determine verdict
    has_critical_issues = any(not f.passed for f in findings if f.check_name in
                              ["claims_have_evidence", "scope_integrity"])
    if has_critical_issues and unsupported > 5:
        verdict = IntegrityVerdict.FAIL
        overall = "failed"
    elif issues or warnings:
        verdict = IntegrityVerdict.PASS_WITH_WARNINGS
        overall = "warnings"
    else:
        verdict = IntegrityVerdict.PASS
        overall = "passed"

    return AuditResult(
        total_claims=total_claims,
        claims_with_evidence_links=claims_with_evidence,
        unsupported_claims=unsupported,
        identifiable_source_metadata=verified_papers,
        citations_total=len(session.papers),
        contradictions_represented=len(session.contradictions) > 0,
        bibliographic_metadata_complete=bib_validated,
        uncertainty_levels_present=has_uncertainty,
        integrity_findings=findings,
        issues=issues,
        warnings=warnings,
        overall_integrity=overall,
        verdict=verdict,
    )


# ─── Research Graph Construction ─────────────────────────

def build_research_graph(session: ResearchSession) -> ResearchGraph:
    """Build the complete research knowledge graph for frontend visualization."""
    nodes = []
    edges = []
    clusters: dict[str, list[str]] = defaultdict(list)

    # Paper nodes
    for pid, paper in session.papers.items():
        nodes.append(GraphNode(
            id=pid, node_type="PAPER", label=paper.title,
            metadata={"year": paper.year, "venue": paper.venue,
                      "research_score": paper.research_score, "citation_count": paper.citation_count}
        ))

    # Claim nodes
    for claim in session.claims:
        nodes.append(GraphNode(
            id=claim.id, node_type="CLAIM", label=claim.statement[:80],
            metadata={"confidence": claim.confidence.value, "metric": claim.metric,
                      "paper_id": claim.paper_id, "status": claim.status}
        ))
        # Paper -> Claim edge
        edges.append(GraphEdge(
            source_id=claim.paper_id, target_id=claim.id,
            edge_type="CONTAINS_CLAIM"
        ))

    # Evidence nodes
    for ev in session.evidence:
        nodes.append(GraphNode(
            id=ev.id, node_type="EVIDENCE", label=ev.description[:80],
            metadata={"type": ev.evidence_type, "metric": ev.metric, "dataset": ev.dataset}
        ))
        edges.append(GraphEdge(
            source_id=ev.id, target_id=ev.claim_id,
            edge_type="SUPPORTS"
        ))

    # Citation edges
    for cite in session.citations:
        edges.append(GraphEdge(
            source_id=cite.source_paper_id, target_id=cite.target_paper_id,
            edge_type="CITES",
            metadata={"relation": cite.relation.value}
        ))

    # Contradiction edges
    for contra in session.contradictions:
        edges.append(GraphEdge(
            source_id=contra.claim_a_id, target_id=contra.claim_b_id,
            edge_type="CONTRADICTS",
            metadata={"type": contra.classification.value, "severity": contra.severity}
        ))

    # Gap nodes
    for gap in session.gaps:
        nodes.append(GraphNode(
            id=gap.id, node_type="GAP", label=gap.title,
            metadata={"type": gap.gap_type, "importance": gap.importance}
        ))
        for pid in gap.supporting_paper_ids:
            edges.append(GraphEdge(
                source_id=pid, target_id=gap.id, edge_type="REVEALS_GAP"
            ))
        clusters["gaps"].append(gap.id)

    # Dead-end nodes
    for de in session.dead_ends:
        nodes.append(GraphNode(
            id=de.id, node_type="DEAD_END", label=de.approach,
            metadata={"status": de.status.value}
        ))
        for pid in de.supporting_papers:
            edges.append(GraphEdge(
                source_id=pid, target_id=de.id, edge_type="DEMONSTRATES_FAILURE"
            ))
        clusters["dead_ends"].append(de.id)

    # Experiment nodes
    if session.experiment:
        exp = session.experiment
        nodes.append(GraphNode(
            id=exp.id, node_type="EXPERIMENT", label=exp.hypothesis[:80],
            metadata={"gap_id": exp.gap_id}
        ))
        if exp.gap_id:
            edges.append(GraphEdge(
                source_id=exp.id, target_id=exp.gap_id, edge_type="ADDRESSES"
            ))

    # Claim propagation edges
    for prop in session.claim_propagations:
        edges.append(GraphEdge(
            source_id=prop.source_claim_id, target_id=prop.derived_claim_id,
            edge_type="PROPAGATED_AS",
            metadata={"type": prop.relationship_type.value}
        ))

    return ResearchGraph(nodes=nodes, edges=edges, clusters=dict(clusters))


# ─── Evidence-Driven Gap Detection (Deterministic Part) ──

def compute_evidence_coverage(session: ResearchSession) -> dict[str, Any]:
    """Compute evidence coverage statistics for gap detection.

    Returns structured data about what is and isn't covered.
    """
    coverage = {
        "datasets_covered": set(),
        "methods_covered": set(),
        "metrics_covered": set(),
        "conditions_covered": set(),
        "methods_by_dataset": defaultdict(set),
        "datasets_by_method": defaultdict(set),
        "cross_domain_studies": 0,
        "uncertainty_studies": 0,
        "reproducibility_available": 0,
        "total_papers": len(session.papers),
    }

    for method in session.methods:
        if method.dataset:
            coverage["datasets_covered"].add(method.dataset)
            if method.model_architecture:
                coverage["methods_by_dataset"][method.dataset].add(method.model_architecture)
                coverage["datasets_by_method"][method.model_architecture].add(method.dataset)
        if method.model_architecture:
            coverage["methods_covered"].add(method.model_architecture)
        for metric in method.metrics:
            coverage["metrics_covered"].add(metric)

    for claim in session.claims:
        for cond in claim.conditions:
            coverage["conditions_covered"].add(cond.lower())
            if any(kw in cond.lower() for kw in ["cross-domain", "transfer", "cross-chemistry"]):
                coverage["cross_domain_studies"] += 1
            if any(kw in cond.lower() for kw in ["uncertainty", "calibration", "confidence interval"]):
                coverage["uncertainty_studies"] += 1

    for pid, analysis in session.analyses.items():
        if analysis.code_availability == Availability.AVAILABLE:
            coverage["reproducibility_available"] += 1

    # Convert sets to lists for JSON serialization
    for key in ["datasets_covered", "methods_covered", "metrics_covered", "conditions_covered"]:
        coverage[key] = sorted(coverage[key])
    for key in ["methods_by_dataset", "datasets_by_method"]:
        coverage[key] = {k: sorted(v) for k, v in coverage[key].items()}

    return coverage
