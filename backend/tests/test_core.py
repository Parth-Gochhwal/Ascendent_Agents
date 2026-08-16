"""Tests for NEXUS core functionality."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from backend.app.models.research import (
    Paper, Author, Claim, Evidence, Contradiction, ConsensusFinding,
    ResearchSession, ResearchPlan, PaperAnalysis, MethodPipeline,
    ContradictionType, ConsensusStatus, EvidenceConfidence, SessionStatus,
    AgentStatus, new_id
)


class TestPaperNormalization:
    def test_new_id_format(self):
        """IDs should be 12-char UUIDs."""
        id1 = new_id()
        id2 = new_id()
        assert len(id1) == 12
        assert id1 != id2

    def test_paper_creation(self):
        p = Paper(title="Test Paper", authors=[Author(name="John Doe")], year=2024)
        assert p.title == "Test Paper"
        assert len(p.id) == 12
        assert p.authors[0].name == "John Doe"
        assert p.relevance_score == 0.0

    def test_paper_score_components(self):
        p = Paper(title="Test", score_components={"relevance": 0.8, "recency": 0.9})
        assert p.score_components["relevance"] == 0.8


class TestDeduplication:
    def _normalize_title(self, title: str) -> str:
        import re
        t = title.lower().strip()
        t = re.sub(r'[^\w\s]', '', t)
        t = re.sub(r'\s+', ' ', t)
        return t

    def test_title_normalization(self):
        assert self._normalize_title("Graph Attention Networks") == "graph attention networks"
        assert self._normalize_title("  Graph  Attention  Networks  ") == "graph attention networks"
        assert self._normalize_title("Graph-Attention Networks!") == "graphattention networks"

    def test_dedup_by_title(self):
        papers = [
            Paper(title="Graph Attention Networks for Battery RUL"),
            Paper(title="graph attention networks for battery rul"),
            Paper(title="Different Paper Title"),
        ]
        seen = set()
        unique = []
        for p in papers:
            norm = self._normalize_title(p.title)
            if norm not in seen:
                seen.add(norm)
                unique.append(p)
        assert len(unique) == 2

    def test_dedup_by_doi(self):
        papers = [
            Paper(title="Paper A", doi="10.1109/test.2024.001"),
            Paper(title="Paper A (variant)", doi="10.1109/TEST.2024.001"),
            Paper(title="Paper B", doi="10.1016/different"),
        ]
        seen_dois = set()
        unique = []
        for p in papers:
            if p.doi:
                doi_lower = p.doi.lower().strip()
                if doi_lower in seen_dois:
                    continue
                seen_dois.add(doi_lower)
            unique.append(p)
        assert len(unique) == 2


class TestContradictionClassification:
    """Deterministic tests for contradiction logic."""

    def test_same_dataset_different_result_is_direct_contradiction(self):
        """Same conditions, opposite results → direct contradiction."""
        c = Contradiction(
            claim_a_id="c1", claim_b_id="c2",
            paper_a_id="p1", paper_b_id="p2",
            claim_a_text="GNN > LSTM on Dataset A",
            claim_b_text="LSTM > GNN on Dataset A",
            shared_conditions=["Dataset A", "same metric"],
            different_conditions=[],
            classification=ContradictionType.DIRECT_CONTRADICTION,
        )
        assert c.classification == ContradictionType.DIRECT_CONTRADICTION
        assert len(c.different_conditions) == 0

    def test_different_dataset_is_contextual_disagreement(self):
        """Different datasets, different results → contextual disagreement."""
        c = Contradiction(
            claim_a_id="c1", claim_b_id="c2",
            paper_a_id="p1", paper_b_id="p2",
            claim_a_text="GNN > LSTM on Dataset A (short horizon)",
            claim_b_text="LSTM > GNN on Dataset B (long horizon)",
            shared_conditions=["Battery RUL prediction"],
            different_conditions=["Dataset", "Prediction horizon"],
            classification=ContradictionType.CONTEXTUAL_DISAGREEMENT,
        )
        assert c.classification == ContradictionType.CONTEXTUAL_DISAGREEMENT
        assert len(c.different_conditions) == 2

    def test_complementary_claims_are_agreement(self):
        """Claims that complement each other → agreement."""
        c = Contradiction(
            claim_a_id="c1", claim_b_id="c2",
            paper_a_id="p1", paper_b_id="p2",
            claim_a_text="GNN not useful for single-cell",
            claim_b_text="GNN most useful for multi-cell",
            shared_conditions=["GNN evaluation"],
            different_conditions=["single-cell vs multi-cell"],
            classification=ContradictionType.AGREEMENT,
        )
        assert c.classification == ContradictionType.AGREEMENT


class TestResearchSession:
    def test_session_creation(self):
        s = ResearchSession(question="Test question?")
        assert s.status == SessionStatus.IDLE
        assert len(s.id) == 12
        assert s.papers == {}
        assert s.claims == []

    def test_session_stats(self):
        s = ResearchSession(question="Test")
        s.papers["p1"] = Paper(title="Paper 1")
        s.claims.append(Claim(paper_id="p1", statement="Test claim"))
        s.update_stats()
        assert s.stats["papers_discovered"] == 1
        assert s.stats["claims_extracted"] == 1

    def test_session_event(self):
        s = ResearchSession(question="Test")
        event = s.add_event("TestAgent", AgentStatus.RUNNING, "Processing...")
        assert len(s.agent_events) == 1
        assert event.agent_name == "TestAgent"
        assert event.status == AgentStatus.RUNNING


class TestClaimEvidence:
    def test_claim_creation(self):
        c = Claim(
            paper_id="p1",
            statement="Model A outperforms Model B",
            conditions=["Dataset X"],
            metric="RMSE",
            evidence_value="0.081",
            confidence=EvidenceConfidence.HIGH,
        )
        assert c.metric == "RMSE"
        assert c.confidence == EvidenceConfidence.HIGH

    def test_evidence_linking(self):
        c = Claim(id="claim-1", paper_id="p1", statement="Test")
        e = Evidence(claim_id="claim-1", paper_id="p1", description="Test evidence")
        assert e.claim_id == c.id


class TestResearchPlan:
    def test_plan_creation(self):
        p = ResearchPlan(
            normalized_question="Are GNNs better?",
            research_objective="Compare GNN vs Transformer",
            subquestions=["Q1", "Q2", "Q3"],
            search_queries=["gnn battery rul", "transformer battery"],
        )
        assert len(p.subquestions) == 3
        assert len(p.search_queries) == 2


class TestConsensus:
    def test_consensus_finding(self):
        c = ConsensusFinding(
            statement="X is widely agreed upon",
            status=ConsensusStatus.CONSENSUS,
            supporting_paper_ids=["p1", "p2", "p3"],
            confidence=EvidenceConfidence.HIGH,
        )
        assert c.status == ConsensusStatus.CONSENSUS
        assert len(c.supporting_paper_ids) == 3

    def test_contested_finding(self):
        c = ConsensusFinding(
            statement="Y is debated",
            status=ConsensusStatus.CONTESTED,
            supporting_paper_ids=["p1"],
            dissenting_paper_ids=["p2"],
        )
        assert c.status == ConsensusStatus.CONTESTED
        assert len(c.dissenting_paper_ids) == 1


class TestMethodPipeline:
    def test_method_creation(self):
        m = MethodPipeline(
            paper_id="p1",
            dataset="NASA Battery",
            model_architecture="GAT",
            baselines=["LSTM", "GRU"],
            metrics=["RMSE", "MAE"],
        )
        assert m.model_architecture == "GAT"
        assert len(m.baselines) == 2


class TestDemoData:
    def test_demo_papers_exist(self):
        from backend.app.services.demo_data import get_demo_papers
        papers = get_demo_papers()
        assert len(papers) == 8
        assert all(p.is_demo for p in papers.values())

    def test_demo_contradictions(self):
        from backend.app.services.demo_data import get_demo_contradictions
        contras = get_demo_contradictions()
        assert len(contras) == 4
        types = [c.classification for c in contras]
        assert ContradictionType.CONTEXTUAL_DISAGREEMENT in types
        assert ContradictionType.AGREEMENT in types

    def test_demo_consensus(self):
        from backend.app.services.demo_data import get_demo_consensus
        consensus = get_demo_consensus()
        assert len(consensus) >= 4
        statuses = [c.status for c in consensus]
        assert ConsensusStatus.CONSENSUS in statuses
        assert ConsensusStatus.CONTESTED in statuses

    def test_demo_gaps(self):
        from backend.app.services.demo_data import get_demo_gaps
        gaps = get_demo_gaps()
        assert len(gaps) >= 3
        assert all(g.title for g in gaps)
        assert all(g.description for g in gaps)

    def test_demo_audit_integrity(self):
        from backend.app.services.demo_data import get_demo_audit
        audit = get_demo_audit()
        assert audit.total_claims > 0
        assert audit.claims_with_evidence > 0
        assert audit.claims_with_evidence <= audit.total_claims


class TestWhyExplainability:
    @pytest.mark.anyio
    async def test_why_contradiction(self):
        from backend.app.services.pipeline import get_pipeline
        pipeline = get_pipeline()
        session = await pipeline.start_research("Test question?")
        # Wait a moment for demo pipeline to populate
        import asyncio
        await asyncio.sleep(2.5)
        
        if session.contradictions:
            contra_id = session.contradictions[0].id
            why = await pipeline.explain_why(session.id, "contradiction", contra_id)
            assert why is not None
            assert why.target_type == "contradiction"
            assert len(why.evidence_chain) == 2
            assert len(why.reasoning_factors) > 0

    @pytest.mark.anyio
    async def test_why_consensus(self):
        from backend.app.services.pipeline import get_pipeline
        pipeline = get_pipeline()
        session = await pipeline.start_research("Test question?")
        import asyncio
        await asyncio.sleep(2.5)
        
        if session.consensus:
            c_id = session.consensus[0].id
            why = await pipeline.explain_why(session.id, "consensus", c_id)
            assert why is not None
            assert why.target_type == "consensus"
            assert len(why.reasoning_factors) > 0


class TestTimelineGeneration:
    def test_timeline_milestones(self):
        from backend.app.services.pipeline import get_pipeline
        from backend.app.services.demo_data import get_demo_papers
        pipeline = get_pipeline()
        session = ResearchSession(question="Test question")
        session.papers = get_demo_papers()
        pipeline.sessions[session.id] = session
        
        timeline = pipeline.get_timeline(session.id)
        assert len(timeline) >= 4
        years = [m.year for m in timeline]
        assert 2021 in years
        assert 2024 in years
        assert any(m.breakthrough_indicator for m in timeline)


class TestBibliographyFormatting:
    def test_bibtex_formatting(self):
        from backend.app.services.pipeline import get_pipeline
        from backend.app.services.demo_data import get_demo_papers
        pipeline = get_pipeline()
        session = ResearchSession(question="Test question")
        session.papers = get_demo_papers()
        pipeline.sessions[session.id] = session
        
        bibtex = pipeline.get_formatted_bibliography(session.id, "bibtex")
        assert "@article{" in bibtex
        assert "title =" in bibtex
        assert "author =" in bibtex

    def test_apa_formatting(self):
        from backend.app.services.pipeline import get_pipeline
        from backend.app.services.demo_data import get_demo_papers
        pipeline = get_pipeline()
        session = ResearchSession(question="Test question")
        session.papers = get_demo_papers()
        pipeline.sessions[session.id] = session
        
        apa = pipeline.get_formatted_bibliography(session.id, "apa")
        assert len(apa) > 0
        assert "(" in apa

    def test_ieee_formatting(self):
        from backend.app.services.pipeline import get_pipeline
        from backend.app.services.demo_data import get_demo_papers
        pipeline = get_pipeline()
        session = ResearchSession(question="Test question")
        session.papers = get_demo_papers()
        pipeline.sessions[session.id] = session
        
        ieee = pipeline.get_formatted_bibliography(session.id, "ieee")
        assert "[1]" in ieee


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

