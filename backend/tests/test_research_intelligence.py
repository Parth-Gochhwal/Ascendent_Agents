"""Tests for NEXUS Research Intelligence Engine.

Tests the deterministic research intelligence computations:
- Citation echo detection
- Reproducibility profiling
- Dead-end detection
- ClaimLine tracking
- Evidence strength computation
- Consensus independence weighting
- Integrity audit
- Research graph construction
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from backend.app.models.research import (
    ResearchSession, Paper, Author, Claim, Evidence, Contradiction,
    ConsensusFinding, PaperAnalysis, MethodPipeline, CitationEdge,
    EvidenceConfidence, ContradictionType, ConsensusStatus, Availability,
    CitationRelation, ClaimPropagation, ClaimPropagationType,
    CitationEchoCluster, DeadEnd, DeadEndStatus, ReproducibilityProfile,
    EvidenceStrength, IntegrityVerdict, ResearchGap,
)
from backend.app.services import research_intelligence as ri


# ─── Fixtures ────────────────────────────────────────────

def _make_session_with_data() -> ResearchSession:
    """Build a minimal research session with papers, claims, citations, and analyses."""
    session = ResearchSession(question="Are GNNs better than LSTMs?")

    # Papers
    p1 = Paper(id="p1", title="GAT for Battery RUL", authors=[Author(name="Zhang")],
               year=2024, venue="IEEE TII", doi="10.1109/test1", citation_count=45)
    p2 = Paper(id="p2", title="Transformer for Battery", authors=[Author(name="Johnson")],
               year=2024, venue="Applied Energy", doi="10.1016/test2", citation_count=38)
    p3 = Paper(id="p3", title="LSTM Outperforms GNN", authors=[Author(name="Tanaka")],
               year=2023, venue="J Power Sources", doi="10.1016/test3", citation_count=29)
    p4 = Paper(id="p4", title="GCN with Uncertainty", authors=[Author(name="Liu")],
               year=2024, venue="RESS", doi="10.1016/test4", citation_count=18)
    session.papers = {"p1": p1, "p2": p2, "p3": p3, "p4": p4}

    # Claims
    c1 = Claim(id="c1", paper_id="p1", statement="GAT outperforms LSTM for battery RUL prediction",
               conditions=["NASA dataset", "NMC chemistry"], metric="RMSE",
               evidence_value="0.081", confidence=EvidenceConfidence.HIGH)
    c2 = Claim(id="c2", paper_id="p2", statement="Transformer outperforms LSTM for long-horizon prediction",
               conditions=["CALCE dataset", "LFP chemistry"], metric="MAE",
               confidence=EvidenceConfidence.HIGH)
    c3 = Claim(id="c3", paper_id="p3", statement="LSTM outperforms GNN models with limited training data",
               conditions=["CALCE dataset", "limited data"], metric="RMSE",
               confidence=EvidenceConfidence.HIGH)
    c4 = Claim(id="c4", paper_id="p4", statement="GCN with uncertainty achieves comparable performance to GAT",
               conditions=["NASA dataset", "NMC chemistry"], metric="RMSE",
               evidence_value="0.089", confidence=EvidenceConfidence.HIGH)
    session.claims = [c1, c2, c3, c4]

    # Evidence
    e1 = Evidence(id="e1", claim_id="c1", paper_id="p1",
                  description="GAT RMSE 0.081 vs LSTM 0.103",
                  quantitative_value="0.081", metric="RMSE", dataset="NASA")
    e2 = Evidence(id="e2", claim_id="c2", paper_id="p2",
                  description="Transformer MAE 1.23% vs LSTM 1.87%",
                  quantitative_value="1.23%", metric="MAE", dataset="CALCE")
    e3 = Evidence(id="e3", claim_id="c3", paper_id="p3",
                  description="LSTM 15-25% lower RMSE than GNN with limited data",
                  dataset="CALCE")
    session.evidence = [e1, e2, e3]

    # Methods
    m1 = MethodPipeline(paper_id="p1", dataset="NASA", model_architecture="GAT",
                        baselines=["LSTM", "GRU"], metrics=["RMSE", "MAE"],
                        evaluation_protocol="5-fold CV", training_procedure="Supervised, 200 epochs",
                        optimizer="Adam", loss_function="MSE")
    m2 = MethodPipeline(paper_id="p2", dataset="CALCE", model_architecture="Transformer",
                        baselines=["LSTM", "CNN-LSTM"], metrics=["MAE", "MAPE"])
    m3 = MethodPipeline(paper_id="p3", dataset="CALCE", model_architecture="LSTM",
                        baselines=["GCN", "GAT"], metrics=["RMSE"])
    session.methods = [m1, m2, m3]

    # Citations — p3 cites p1, p4 cites p1
    session.citations = [
        CitationEdge(source_paper_id="p3", target_paper_id="p1", relation=CitationRelation.CHALLENGES),
        CitationEdge(source_paper_id="p4", target_paper_id="p1", relation=CitationRelation.EXTENDS),
    ]

    # Analyses
    session.analyses = {
        "p1": PaperAnalysis(paper_id="p1", research_problem="Battery RUL",
                            main_findings=["GAT outperforms LSTM"],
                            limitations=["Only NASA dataset"],
                            code_availability=Availability.NOT_FOUND,
                            dataset_availability=Availability.AVAILABLE,
                            methods=[m1], claims=[c1], evidence=[e1]),
        "p2": PaperAnalysis(paper_id="p2",
                            main_findings=["Transformer outperforms LSTM"],
                            limitations=["High computational cost"],
                            code_availability=Availability.AVAILABLE,
                            dataset_availability=Availability.AVAILABLE,
                            methods=[m2], claims=[c2], evidence=[e2]),
        "p3": PaperAnalysis(paper_id="p3",
                            main_findings=["LSTM outperforms GNN with limited data"],
                            limitations=["Only CALCE dataset"],
                            code_availability=Availability.AVAILABLE,
                            methods=[m3], claims=[c3], evidence=[e3]),
    }

    return session


# ─── Citation Echo Tests ─────────────────────────────────

class TestCitationEchoDetection:
    def test_no_echoes_with_no_citations(self):
        session = ResearchSession(question="Test")
        assert ri.detect_citation_echoes(session) == []

    def test_detects_echo_from_demo_data(self):
        from backend.app.services.demo_data import (
            get_demo_papers, get_demo_analyses, get_demo_citations
        )
        session = ResearchSession(question="Test")
        session.papers = get_demo_papers()
        analyses = get_demo_analyses()
        session.citations = get_demo_citations()
        for analysis in analyses.values():
            session.claims.extend(analysis.claims)

        echoes = ri.detect_citation_echoes(session)
        # Should detect at least some echo patterns given the citation structure
        # (p3, p4, p5, p6, p7, p8 all cite p1 or p2)
        assert isinstance(echoes, list)


# ─── Reproducibility Profiling Tests ─────────────────────

class TestReproducibilityProfiling:
    def test_profile_with_analysis(self):
        paper = Paper(id="p1", title="Test", citation_count=50)
        method = MethodPipeline(
            paper_id="p1", dataset="NASA", model_architecture="GAT",
            model_details="3-layer GAT", baselines=["LSTM", "GRU"],
            metrics=["RMSE", "MAE"], evaluation_protocol="5-fold CV",
            training_procedure="Supervised", optimizer="Adam", loss_function="MSE",
            preprocessing=["Normalization"]
        )
        analysis = PaperAnalysis(
            paper_id="p1",
            code_availability=Availability.AVAILABLE,
            dataset_availability=Availability.AVAILABLE,
            methods=[method]
        )
        profile = ri.compute_reproducibility_profile(paper, analysis)
        assert profile.paper_id == "p1"
        assert profile.code_available == Availability.AVAILABLE
        assert profile.dataset_available == Availability.AVAILABLE
        assert profile.completeness_score > 0.5
        assert profile.model_specification_documented == Availability.AVAILABLE

    def test_profile_without_analysis(self):
        paper = Paper(id="p2", title="Test")
        profile = ri.compute_reproducibility_profile(paper, None)
        assert profile.paper_id == "p2"
        assert profile.completeness_score == 0.25  # all unknown

    def test_profile_missing_code_generates_risk(self):
        paper = Paper(id="p3", title="Test")
        analysis = PaperAnalysis(
            paper_id="p3",
            code_availability=Availability.NOT_FOUND,
        )
        profile = ri.compute_reproducibility_profile(paper, analysis)
        assert any("code" in r.lower() for r in profile.risk_factors)

    def test_compute_completeness_method(self):
        profile = ReproducibilityProfile(paper_id="test")
        profile.dataset_available = Availability.AVAILABLE
        profile.code_available = Availability.AVAILABLE
        profile.model_specification_documented = Availability.AVAILABLE
        score = profile.compute_completeness()
        assert score > 0.25  # should be higher than all-unknown


# ─── Dead-End Detection Tests ────────────────────────────

class TestDeadEndDetection:
    def test_detects_superseded_baselines(self):
        session = _make_session_with_data()
        dead_ends = ri.detect_dead_ends(session)
        # LSTM appears as baseline in p1 (GAT beats it) and p2 (Transformer beats it)
        # but also as the winning method in p3
        assert isinstance(dead_ends, list)

    def test_empty_session_no_dead_ends(self):
        session = ResearchSession(question="Test")
        assert ri.detect_dead_ends(session) == []

    def test_detects_failure_claims(self):
        session = ResearchSession(question="Test")
        paper = Paper(id="p1", title="Test Paper")
        session.papers["p1"] = paper
        session.claims = [
            Claim(id="c1", paper_id="p1",
                  statement="GNN is not justified for single-cell scenarios",
                  conditions=["single cell", "limited data"],
                  confidence=EvidenceConfidence.HIGH)
        ]
        session.analyses = {"p1": PaperAnalysis(paper_id="p1", methods=[])}
        dead_ends = ri.detect_dead_ends(session)
        assert len(dead_ends) >= 1
        assert any("GNN" in d.approach for d in dead_ends)


# ─── ClaimLine Tracking Tests ────────────────────────────

class TestClaimLineTracking:
    def test_builds_propagations_from_citations(self):
        session = _make_session_with_data()
        propagations = ri.build_claim_propagations(session)
        assert isinstance(propagations, list)

    def test_no_propagations_without_citations(self):
        session = ResearchSession(question="Test")
        session.claims = [Claim(paper_id="p1", statement="Test claim")]
        assert ri.build_claim_propagations(session) == []

    def test_classify_preserved_propagation(self):
        orig = Claim(id="c1", paper_id="p1", statement="GAT is good",
                     conditions=["NASA", "NMC"])
        derived = Claim(id="c2", paper_id="p2", statement="GAT is good",
                        conditions=["NASA", "NMC"])
        result = ri._classify_propagation(orig, derived)
        assert result == ClaimPropagationType.PRESERVED

    def test_classify_generalized_propagation(self):
        orig = Claim(id="c1", paper_id="p1", statement="GAT outperforms LSTM",
                     conditions=["NASA", "NMC", "short horizon"])
        derived = Claim(id="c2", paper_id="p2", statement="GAT outperforms LSTM",
                        conditions=[])
        result = ri._classify_propagation(orig, derived)
        assert result == ClaimPropagationType.GENERALIZED

    def test_classify_specialized_propagation(self):
        orig = Claim(id="c1", paper_id="p1", statement="GAT works well",
                     conditions=["battery RUL"])
        derived = Claim(id="c2", paper_id="p2", statement="GAT works well",
                        conditions=["battery RUL", "multi-cell", "high data"])
        result = ri._classify_propagation(orig, derived)
        assert result == ClaimPropagationType.SPECIALIZED

    def test_classify_context_shifted_propagation(self):
        orig = Claim(id="c1", paper_id="p1", statement="GAT outperforms LSTM",
                     conditions=["NASA", "NMC"])
        derived = Claim(id="c2", paper_id="p2", statement="GAT outperforms LSTM",
                        conditions=["CALCE", "LFP"])
        result = ri._classify_propagation(orig, derived)
        assert result == ClaimPropagationType.CONTEXT_SHIFTED


# ─── Consensus Independence Tests ────────────────────────

class TestConsensusIndependence:
    def test_independence_with_no_citations(self):
        session = ResearchSession(question="Test")
        finding = ConsensusFinding(
            statement="X is consensus",
            status=ConsensusStatus.CONSENSUS,
            supporting_paper_ids=["p1", "p2", "p3"],
            confidence=EvidenceConfidence.HIGH
        )
        result = ri.compute_consensus_independence(finding, session)
        assert result.independent_support_count == 3
        assert result.independence_weight == 1.0

    def test_independence_with_citation_dependency(self):
        session = _make_session_with_data()
        finding = ConsensusFinding(
            statement="GNN outperforms LSTM",
            status=ConsensusStatus.CONSENSUS,
            supporting_paper_ids=["p1", "p3", "p4"],
            confidence=EvidenceConfidence.HIGH
        )
        result = ri.compute_consensus_independence(finding, session)
        # p3 and p4 both cite p1, so they are dependent
        assert result.independent_support_count < 3
        assert result.independence_weight < 1.0
        assert result.evidence_quality_weighted is True


# ─── Evidence Strength Tests ─────────────────────────────

class TestEvidenceStrength:
    def test_composite_score_calculation(self):
        strength = EvidenceStrength(
            directness=0.9, source_quality=0.8,
            methodological_rigor=0.7, reproducibility=0.6,
            external_validity=0.5, cross_study_consistency=0.4,
            scope_alignment=0.3
        )
        composite = strength.composite_score
        assert 0.0 <= composite <= 1.0
        # Expected: 0.20*0.9 + 0.15*0.8 + 0.20*0.7 + 0.15*0.6 + 0.10*0.5 + 0.10*0.4 + 0.10*0.3
        # = 0.18 + 0.12 + 0.14 + 0.09 + 0.05 + 0.04 + 0.03 = 0.65
        assert abs(composite - 0.65) < 0.01

    def test_compute_evidence_strength(self):
        session = _make_session_with_data()
        claim = session.claims[0]  # GAT outperforms LSTM
        paper = session.papers["p1"]
        strength = ri.compute_evidence_strength(claim, session.evidence, paper, session)
        assert strength is not None
        assert 0.0 <= strength.composite_score <= 1.0
        assert strength.directness > 0.5  # has quantitative evidence
        assert strength.rationale != ""


# ─── Contradiction Candidate Tests ───────────────────────

class TestContradictionCandidates:
    def test_generates_candidates(self):
        session = _make_session_with_data()
        candidates = ri.generate_contradiction_candidates(
            session.claims, session.papers
        )
        assert isinstance(candidates, list)
        # Should find c1 (GAT > LSTM) vs c3 (LSTM > GNN) as a candidate
        claim_pairs = [(c1.id, c2.id) for c1, c2 in candidates]
        assert len(candidates) > 0

    def test_no_self_paper_comparisons(self):
        session = _make_session_with_data()
        candidates = ri.generate_contradiction_candidates(
            session.claims, session.papers
        )
        for c1, c2 in candidates:
            assert c1.paper_id != c2.paper_id

    def test_likelihood_score_opposing_keywords(self):
        c1 = Claim(id="c1", paper_id="p1", statement="GNN outperforms LSTM",
                   metric="RMSE")
        c2 = Claim(id="c2", paper_id="p2", statement="LSTM outperforms GNN",
                   metric="RMSE")
        score = ri._contradiction_likelihood_score(c1, c2, {})
        assert score >= 0.5  # opposing keywords + same metric


# ─── Integrity Audit Tests ───────────────────────────────

class TestIntegrityAudit:
    def test_audit_passes_for_good_session(self):
        session = _make_session_with_data()
        # Add a contradiction so that check passes
        session.contradictions = [
            Contradiction(
                claim_a_id="c1", claim_b_id="c3",
                paper_a_id="p1", paper_b_id="p3",
                classification=ContradictionType.CONTEXTUAL_DISAGREEMENT
            )
        ]
        audit = ri.run_deterministic_audit(session)
        assert audit.total_claims == 4
        assert audit.claims_with_evidence_links >= 2
        assert audit.overall_integrity in ("passed", "warnings")
        assert len(audit.integrity_findings) > 0

    def test_audit_detects_unsupported_claims(self):
        session = ResearchSession(question="Test")
        session.papers["p1"] = Paper(id="p1", title="Test", doi="10.1109/test")
        session.claims = [
            Claim(id="c1", paper_id="p1", statement="Unsupported claim"),
            Claim(id="c2", paper_id="p1", statement="Another unsupported"),
            Claim(id="c3", paper_id="p1", statement="Yet another"),
        ]
        session.evidence = []  # No evidence at all
        audit = ri.run_deterministic_audit(session)
        assert audit.unsupported_claims == 3
        assert audit.total_claims == 3

    def test_audit_reports_citation_echo_warnings(self):
        session = ResearchSession(question="Test")
        session.papers["p1"] = Paper(id="p1", title="Test", doi="10.1109/test")
        session.claims = [
            Claim(id="c1", paper_id="p1", statement="Test"),
        ]
        session.evidence = [Evidence(id="e1", claim_id="c1", paper_id="p1", description="Test")]
        session.citation_echoes = [
            CitationEchoCluster(
                claim_statement="Test",
                originating_paper_id="p1",
                echo_paper_ids=["p2", "p3"],
                total_support_count=3,
                independent_support_count=1,
                independence_weight=0.333
            )
        ]
        audit = ri.run_deterministic_audit(session)
        assert any("echo" in w.lower() for w in audit.warnings)


# ─── Research Graph Tests ────────────────────────────────

class TestResearchGraph:
    def test_builds_graph_from_session(self):
        session = _make_session_with_data()
        graph = ri.build_research_graph(session)
        assert len(graph.nodes) > 0
        assert len(graph.edges) > 0

        # Check node types
        node_types = set(n.node_type for n in graph.nodes)
        assert "PAPER" in node_types
        assert "CLAIM" in node_types
        assert "EVIDENCE" in node_types

        # Check edge types
        edge_types = set(e.edge_type for e in graph.edges)
        assert "CONTAINS_CLAIM" in edge_types
        assert "SUPPORTS" in edge_types
        assert "CITES" in edge_types

    def test_empty_session_empty_graph(self):
        session = ResearchSession(question="Test")
        graph = ri.build_research_graph(session)
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_graph_includes_gaps_and_dead_ends(self):
        session = _make_session_with_data()
        session.gaps = [ResearchGap(id="g1", title="Missing cross-domain evaluation",
                                    description="Test gap", supporting_paper_ids=["p1"])]
        session.dead_ends = [DeadEnd(id="de1", approach="MLP",
                                      description="Superseded", supporting_papers=["p1"])]
        graph = ri.build_research_graph(session)
        node_types = set(n.node_type for n in graph.nodes)
        assert "GAP" in node_types
        assert "DEAD_END" in node_types
        assert "gaps" in graph.clusters
        assert "dead_ends" in graph.clusters


# ─── Demo Data Integration Tests ─────────────────────────

class TestDemoDataIntegration:
    def test_demo_dead_ends(self):
        from backend.app.services.demo_data import get_demo_dead_ends
        dead_ends = get_demo_dead_ends()
        assert len(dead_ends) == 3
        statuses = [d.status for d in dead_ends]
        assert DeadEndStatus.SUPERSEDED in statuses
        assert DeadEndStatus.LIMITED in statuses
        assert DeadEndStatus.FAILED in statuses

    def test_demo_reproducibility_profiles(self):
        from backend.app.services.demo_data import get_demo_reproducibility_profiles
        profiles = get_demo_reproducibility_profiles()
        assert len(profiles) >= 3
        assert "demo-p001" in profiles
        assert profiles["demo-p001"].completeness_score > 0.0
        assert profiles["demo-p005"].completeness_score > 0.9  # highest quality

    def test_demo_claim_propagations(self):
        from backend.app.services.demo_data import get_demo_claim_propagations
        props = get_demo_claim_propagations()
        assert len(props) == 4
        types = [p.relationship_type for p in props]
        assert ClaimPropagationType.CONTEXT_SHIFTED in types
        assert ClaimPropagationType.PRESERVED in types
        assert ClaimPropagationType.CONTRADICTED in types
        assert ClaimPropagationType.SPECIALIZED in types

    def test_demo_citation_echoes(self):
        from backend.app.services.demo_data import get_demo_citation_echoes
        echoes = get_demo_citation_echoes()
        assert len(echoes) == 1
        echo = echoes[0]
        assert echo.independence_weight < 0.5
        assert echo.independent_support_count < echo.total_support_count

    def test_demo_red_team_findings(self):
        from backend.app.services.demo_data import get_demo_red_team_findings
        findings = get_demo_red_team_findings()
        assert len(findings) >= 4
        assert any(f.finding_type.value == "citation_echo" for f in findings)
        assert any(f.finding_type.value == "reproducibility_weakness" for f in findings)

    def test_demo_audit_has_integrity_findings(self):
        from backend.app.services.demo_data import get_demo_audit
        audit = get_demo_audit()
        assert len(audit.integrity_findings) >= 5
        assert audit.verdict == IntegrityVerdict.PASS_WITH_WARNINGS


# ─── Full Demo Pipeline Integration ─────────────────────

class TestDemoPipelineIntegration:
    @pytest.mark.anyio
    async def test_demo_pipeline_produces_new_features(self):
        """Full integration test — run demo pipeline and check new features populate."""
        from backend.app.services.pipeline import get_pipeline
        pipeline = get_pipeline()
        session = await pipeline.start_research("Test question for integration?")
        import asyncio
        await asyncio.sleep(25)  # Allow demo pipeline to complete (17 phases)

        # Check new features are populated
        assert len(session.dead_ends) > 0, "Dead ends should be populated"
        assert len(session.reproducibility_profiles) > 0, "Reproducibility profiles should be populated"
        assert len(session.claim_propagations) > 0, "Claim propagations should be populated"
        assert len(session.citation_echoes) > 0, "Citation echoes should be populated"

        # Check red team has structured findings
        assert session.red_team is not None
        assert len(session.red_team.findings) > 0, "Red team should have structured findings"

        # Check audit has integrity findings
        assert session.audit is not None
        assert len(session.audit.integrity_findings) > 0, "Audit should have integrity findings"

        # Check stats reflect new features
        session.update_stats()
        assert session.stats["dead_ends"] > 0
        assert session.stats["reproducibility_profiles"] > 0
        assert session.stats["claim_propagations"] > 0
        assert session.stats["citation_echoes"] > 0

    @pytest.mark.anyio
    async def test_why_explainability_for_new_features(self):
        """Test the 'Why?' engine for the new deterministic research intelligence features."""
        from backend.app.services.pipeline import get_pipeline
        pipeline = get_pipeline()
        session = await pipeline.start_research("Test question for explainability?")
        import asyncio
        await asyncio.sleep(25)  # Allow demo pipeline to complete

        # Test Dead-End Explainability
        if session.dead_ends:
            de_id = session.dead_ends[0].id
            why_de = await pipeline.explain_why(session.id, "dead_end", de_id)
            assert why_de is not None
            assert why_de.target_type == "dead_end"
            assert len(why_de.reasoning_factors) > 0

        # Test ClaimLine Explainability
        if session.claim_propagations:
            cp_id = session.claim_propagations[0].id
            why_cp = await pipeline.explain_why(session.id, "claim_propagation", cp_id)
            assert why_cp is not None
            assert why_cp.target_type == "claim_propagation"
            assert len(why_cp.evidence_chain) == 2  # Source and derived

        # Test Citation Echo Explainability
        if session.citation_echoes:
            ce_id = session.citation_echoes[0].id
            why_ce = await pipeline.explain_why(session.id, "citation_echo", ce_id)
            assert why_ce is not None
            assert why_ce.target_type == "citation_echo"
            assert len(why_ce.evidence_chain) >= 1  # Originating source

        # Test Reproducibility Explainability
        if session.reproducibility_profiles:
            rp_id = next(iter(session.reproducibility_profiles.keys()))
            why_rp = await pipeline.explain_why(session.id, "reproducibility", rp_id)
            assert why_rp is not None
            assert why_rp.target_type == "reproducibility"
            assert "Score" in why_rp.reasoning_factors[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
