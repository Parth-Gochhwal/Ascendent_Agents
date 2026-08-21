"""Comprehensive unit and integration tests for NEXUS Agents."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.app.models.research import (
    ResearchSession, ResearchPlan, Paper, PaperAnalysis, Claim, Evidence,
    MethodPipeline, Contradiction, ConsensusFinding, ResearchGap,
    MissingExperiment, NoveltyAssessment, ExperimentProposal, RedTeamResult,
    RedTeamFinding, ContradictionType, ConsensusStatus, EvidenceConfidence,
    DeadEnd, DeadEndStatus, Availability
)
from backend.app.services.agents import (
    BaseAgent, PlanningAgent, RetrievalAgent, AnalysisAgent,
    IntelligenceAgent, SynthesisAgent, InnovationAgent, RedTeamAgent
)
from backend.app.providers.academic import AcademicSearchProvider


class MockProvider(AcademicSearchProvider):
    def __init__(self, name: str, should_fail: bool = False, papers: list = None):
        self.name_val = name
        self.should_fail = should_fail
        self.papers = papers or []

    @property
    def provider_name(self) -> str:
        return self.name_val

    async def search(self, query: str, max_results: int = 25) -> list[Paper]:
        if self.should_fail:
            raise RuntimeError(f"Simulated network error for {self.name_val}")
        return self.papers

    async def get_paper(self, paper_id: str):
        for p in self.papers:
            if p.id == paper_id:
                return p
        return None


@pytest.mark.anyio
async def test_planning_agent():
    mock_llm = MagicMock()
    mock_plan = ResearchPlan(
        normalized_question="What are efficient transformer architectures?",
        research_objective="Evaluate sparse vs linear attention mechanisms.",
        subquestions=["What is linear attention?", "How does sparse attention compare?"],
        search_queries=["efficient transformers", "linear attention", "sparse attention"]
    )
    mock_llm.structured_generate = AsyncMock(return_value=mock_plan)

    agent = PlanningAgent(mock_llm)
    assert agent.name == "Planning Agent"

    session = ResearchSession(question="What are efficient transformer architectures?")
    await agent.execute(session)

    assert session.plan is not None
    assert len(session.plan.subquestions) == 2
    assert len(session.plan.search_queries) == 3
    mock_llm.structured_generate.assert_called_once()


@pytest.mark.anyio
async def test_retrieval_agent_provider_isolation():
    """Verify that if one provider fails, the others continue and papers are deduplicated & ranked."""
    p1 = Paper(id="p1", title="Sparse Transformers", doi="10.1145/1", citation_count=50, year=2023, abstract="A study of sparse attention.")
    p2 = Paper(id="p2", title="Sparse Transformers", doi="10.1145/1", citation_count=50, year=2023, abstract="Duplicate copy.")
    p3 = Paper(id="p3", title="Linear Attention in Practice", doi="10.1145/2", citation_count=100, year=2024, abstract="Linear attention complexities.")

    prov1 = MockProvider("failing_provider", should_fail=True)
    prov2 = MockProvider("working_provider_a", should_fail=False, papers=[p1, p2])
    prov3 = MockProvider("working_provider_b", should_fail=False, papers=[p3])

    agent = RetrievalAgent(llm=MagicMock(), providers=[prov1, prov2, prov3], max_papers=10)
    assert agent.name == "Literature Discovery"

    session = ResearchSession(question="sparse linear attention")
    session.plan = ResearchPlan(
        normalized_question="sparse linear attention",
        research_objective="Test",
        search_queries=["sparse transformers", "linear attention"]
    )

    found, deduped, selected = await agent.execute(session)
    assert found == 6
    assert deduped == 2
    assert selected == 2
    assert len(session.papers) == 2
    assert "p1" in session.papers
    assert "p3" in session.papers
    # Verify ranking scores computed deterministically
    assert session.papers["p1"].research_score is not None
    assert session.papers["p3"].research_score is not None


@pytest.mark.anyio
async def test_analysis_agent():
    mock_llm = MagicMock()
    mock_analysis = PaperAnalysis(
        paper_id="p1",
        main_findings=["Linear attention reduces memory to O(N)."],
        limitations=["May degrade autoregressive generation quality."]
    )
    mock_claims = MagicMock()
    mock_claims.claims = [Claim(id="c1", statement="Linear attention has O(N) complexity.", paper_id="p1")]
    mock_method = MethodPipeline(id="m1", paper_id="p1", model_architecture="Linear Transformer", dataset="WikiText-103")

    mock_llm.structured_generate = AsyncMock(side_effect=[mock_analysis, mock_claims, mock_method])

    agent = AnalysisAgent(mock_llm)
    session = ResearchSession(question="linear attention complexity")
    session.papers["p1"] = Paper(id="p1", title="Linear Transformers", abstract="We present linear transformers.")

    await agent.execute(session)

    assert "p1" in session.analyses
    assert len(session.claims) == 1
    assert session.claims[0].statement == "Linear attention has O(N) complexity."
    assert len(session.methods) == 1
    assert session.methods[0].model_architecture == "Linear Transformer"


@pytest.mark.anyio
async def test_intelligence_agent():
    """Verify deterministic intelligence computations without LLM calls."""
    agent = IntelligenceAgent(llm=MagicMock())
    session = ResearchSession(question="Transformers")
    p1 = Paper(id="p1", title="Sparse Attention", doi="10.1/a", year=2021, abstract="Baseline sparse attention.")
    p2 = Paper(id="p2", title="Improved Sparse Attention", doi="10.1/b", year=2023, abstract="We cite Sparse Attention.")
    session.papers = {"p1": p1, "p2": p2}
    session.claims = [
        Claim(id="c1", statement="Sparse attention achieves 2x speedup.", paper_id="p1", confidence=EvidenceConfidence.HIGH),
        Claim(id="c2", statement="Sparse attention achieves 2x speedup.", paper_id="p2", confidence=EvidenceConfidence.HIGH)
    ]
    session.analyses = {
        "p1": PaperAnalysis(paper_id="p1", code_availability=Availability.AVAILABLE, dataset_availability=Availability.AVAILABLE),
        "p2": PaperAnalysis(paper_id="p2", code_availability=Availability.NOT_FOUND, dataset_availability=Availability.AVAILABLE)
    }

    # Pre-synthesis execution
    await agent.execute(session, phase="pre_synthesis")
    assert len(session.citations) >= 1
    assert "p1" in session.reproducibility_profiles
    assert session.reproducibility_profiles["p1"].completeness_score > 0
    assert len(session.claims[0].strength.rationale) > 0

    # Post-synthesis execution (audit)
    await agent.execute(session, phase="post_synthesis")
    assert session.audit is not None
    assert session.audit.total_claims == 2


@pytest.mark.anyio
async def test_synthesis_agent():
    mock_llm = MagicMock()
    mock_contra_list = MagicMock()
    mock_contra_list.contradictions = [
        Contradiction(
            id="contra1",
            claim_a_id="c1",
            claim_b_id="c2",
            paper_a_id="p1",
            paper_b_id="p2",
            claim_a_text="Linear attention matches full attention.",
            claim_b_text="Linear attention suffers large perplexity degradation.",
            classification=ContradictionType.CONTEXTUAL_DISAGREEMENT,
            explanation="Different sequence lengths were evaluated."
        )
    ]
    mock_consensus_list = MagicMock()
    mock_consensus_list.findings = [
        ConsensusFinding(
            id="cons1",
            statement="Subquadratic attention significantly reduces memory footprint.",
            status=ConsensusStatus.CONSENSUS,
            supporting_paper_ids=["p1", "p2"]
        )
    ]
    mock_llm.structured_generate = AsyncMock(side_effect=[mock_contra_list, mock_consensus_list])

    agent = SynthesisAgent(mock_llm)
    session = ResearchSession(question="Linear attention")
    session.papers = {
        "p1": Paper(id="p1", title="Paper A"),
        "p2": Paper(id="p2", title="Paper B")
    }
    session.claims = [
        Claim(id="c1", statement="Linear attention matches full attention.", paper_id="p1"),
        Claim(id="c2", statement="Linear attention suffers large perplexity degradation.", paper_id="p2")
    ]

    await agent.execute(session)
    assert len(session.contradictions) == 1
    assert session.contradictions[0].classification == ContradictionType.CONTEXTUAL_DISAGREEMENT
    assert len(session.consensus) == 1
    assert session.consensus[0].status == ConsensusStatus.CONSENSUS


@pytest.mark.anyio
async def test_innovation_agent_with_dead_ends_and_novelty():
    mock_llm = MagicMock()
    mock_gaps = MagicMock()
    mock_gaps.gaps = [
        ResearchGap(
            id="g1",
            title="Long-context retrieval failure in linear attention",
            description="Linear attention mechanisms fail to recall exact needle-in-haystack keys above 32k tokens."
        )
    ]
    mock_missing = MagicMock()
    mock_missing.experiments = [
        MissingExperiment(
            id="me1",
            method="Hybrid State Space with Chunked KV",
            dataset="LRA Benchmark",
            condition="32k-128k sequence length"
        )
    ]
    mock_novelty = NoveltyAssessment(
        id="nov1",
        assessment="potentially_promising",
        explored_dimensions=["Standard linear RNNs", "Sliding window attention"],
        potentially_unexplored=["Hybrid chunked state-space key retention"]
    )
    mock_proposal = ExperimentProposal(
        id="exp1",
        gap_id="g1",
        hypothesis="Chunked key caching restores needle retrieval accuracy while maintaining linear complexity.",
        research_objective="Benchmark hybrid chunked KV linear attention on 64k tokens.",
        datasets=["Needle-in-a-Haystack", "PG-19"],
        baseline_models=["Standard Transformer", "Mamba-2", "Linear Transformer"],
        evaluation_metrics=["Recall@1", "Perplexity", "Memory Peak"]
    )

    mock_llm.structured_generate = AsyncMock(side_effect=[mock_gaps, mock_missing, mock_novelty, mock_proposal])

    agent = InnovationAgent(mock_llm)
    session = ResearchSession(question="Long-context linear attention")
    session.papers["p1"] = Paper(id="p1", title="Linear RNNs")
    session.dead_ends = [
        DeadEnd(id="de1", approach="Pure Recurrent Attention", description="Catastrophic forgetting at long horizons.", status=DeadEndStatus.SUPERSEDED)
    ]

    await agent.execute(session)

    assert len(session.gaps) == 1
    assert len(session.missing_experiments) == 1
    assert session.novelty is not None
    assert session.novelty.assessment == "potentially_promising"
    assert session.experiment is not None
    assert session.experiment.gap_id == "g1"
    assert "de1" in session.experiment.dead_end_ids


@pytest.mark.anyio
async def test_red_team_agent():
    mock_llm = MagicMock()
    mock_rt = RedTeamResult(
        conclusion_challenged="Subquadratic attention replaces full attention everywhere.",
        challenges=["Evaluations are limited to synthetic associative recall tasks.", "Out-of-domain generalization unproven."],
        weak_evidence=["No empirical results on formal reasoning datasets."],
        final_confidence=EvidenceConfidence.MEDIUM,
        adjudication="Promising for standard pretraining, but requires strict validation on multi-step reasoning."
    )
    mock_llm.structured_generate = AsyncMock(return_value=mock_rt)

    agent = RedTeamAgent(mock_llm)
    session = ResearchSession(question="Subquadratic attention")
    session.consensus = [ConsensusFinding(statement="Subquadratic attention achieves parity with full transformers.")]
    session.evidence = [Evidence(id="e1", claim_id="c1", paper_id="p1", description="Evaluated on synthetic LRA benchmark.")]

    await agent.execute(session)

    assert session.red_team is not None
    assert session.red_team.final_confidence == EvidenceConfidence.MEDIUM
    assert len(session.red_team.challenges) == 2
    assert len(session.red_team.findings) >= 2
    assert session.red_team.findings[0].description == "Evaluations are limited to synthetic associative recall tasks."
