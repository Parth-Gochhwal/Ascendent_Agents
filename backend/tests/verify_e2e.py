"""End-to-End System Verification Script for NEXUS."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


from backend.app.services.pipeline import get_pipeline
from backend.app.models.research import SessionStatus


async def main():
    print("🔬 Starting NEXUS End-to-End Verification...")
    pipeline = get_pipeline()
    
    question = "Are graph neural networks genuinely better than transformer-based models for battery remaining useful life prediction under cross-domain conditions?"
    print(f"1. Starting research session for question: '{question[:60]}...'")
    session = await pipeline.start_research(question)
    assert session.id, "Session ID should exist"
    print(f"   ✓ Session created: {session.id}")
    
    # Wait for demo pipeline to run all 13 phases
    print("2. Monitoring agent execution pipeline...")
    max_wait = 20
    for i in range(max_wait):
        await asyncio.sleep(1.0)
        curr = pipeline.get_session(session.id)
        print(f"   [t={i+1}s] Status: {curr.status.value}, Events: {len(curr.agent_events)}, Papers: {len(curr.papers)}")
        if curr.status in [SessionStatus.REPORT_READY, SessionStatus.ERROR]:
            break
            
    assert curr.status == SessionStatus.REPORT_READY, f"Session should be report_ready, got {curr.status}"
    print(f"   ✓ Pipeline completed successfully with status: {curr.status.value}")
    
    # Verify core entities
    print("3. Verifying research knowledge artifacts:")
    print(f"   - Papers analyzed: {len(curr.papers)} (Expected >= 8)")
    assert len(curr.papers) >= 8
    
    print(f"   - Claims extracted: {len(curr.claims)} (Expected >= 15)")
    assert len(curr.claims) >= 15
    
    print(f"   - Contradictions detected: {len(curr.contradictions)} (Expected >= 3)")
    assert len(curr.contradictions) >= 3
    
    print(f"   - Consensus findings: {len(curr.consensus)} (Expected >= 4)")
    assert len(curr.consensus) >= 4
    
    print(f"   - Research gaps: {len(curr.gaps)} (Expected >= 3)")
    assert len(curr.gaps) >= 3
    
    print(f"   - Missing experiments: {len(curr.missing_experiments)} (Expected >= 2)")
    assert len(curr.missing_experiments) >= 2
    
    assert curr.experiment is not None, "Experiment proposal should exist"
    print(f"   - Experiment designed: '{curr.experiment.hypothesis[:50]}...'")
    
    assert curr.red_team is not None, "Red team result should exist"
    print(f"   - Red team adjudication: '{curr.red_team.adjudication[:50]}...'")
    
    assert curr.audit is not None, "Integrity audit should exist"
    print(f"   - Integrity audit: {curr.audit.overall_integrity.upper()} (Verified {curr.audit.claims_with_evidence}/{curr.audit.total_claims} claims)")

    # Verify 'Why?' Explainability
    print("4. Verifying 'Why?' Explainability Engine:")
    contra_id = curr.contradictions[0].id
    why_contra = await pipeline.explain_why(curr.id, "contradiction", contra_id)
    assert why_contra is not None, "Why explanation for contradiction should exist"
    assert len(why_contra.evidence_chain) >= 2, "Evidence chain should contain both conflicting studies"
    print(f"   ✓ Contradiction Explainability verified: {len(why_contra.evidence_chain)} evidence links, {len(why_contra.reasoning_factors)} reasoning factors")
    
    why_gap = await pipeline.explain_why(curr.id, "gap", curr.gaps[0].id)
    assert why_gap is not None, "Why explanation for research gap should exist"
    print(f"   ✓ Gap Explainability verified: '{why_gap.target_statement}'")

    # Verify Longitudinal Timeline
    print("5. Verifying Longitudinal Timeline Generator:")
    timeline = pipeline.get_timeline(curr.id)
    assert len(timeline) >= 5, "Timeline should contain at least 5 milestones"
    print(f"   ✓ Timeline generated {len(timeline)} chronological milestones (2019 - 2026)")

    # Verify Bibliography Formatter
    print("6. Verifying Multi-Style Bibliography Formatter:")
    bibtex = pipeline.get_formatted_bibliography(curr.id, "bibtex")
    apa = pipeline.get_formatted_bibliography(curr.id, "apa")
    ieee = pipeline.get_formatted_bibliography(curr.id, "ieee")
    assert "@article{" in bibtex
    assert len(apa) > 0
    assert "[1]" in ieee
    print("   ✓ APA, IEEE, and BibTeX formatters validated")

    print("\n🎉 ALL NEXUS VERIFICATION TESTS PASSED PERFECTLY!")


if __name__ == "__main__":
    asyncio.run(main())
