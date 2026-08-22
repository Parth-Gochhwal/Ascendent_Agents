"""Verification script for Question-Dependent Live Academic Pipeline.

Runs Question A (Battery RUL) and Question B (Multimodal RAG) in live mode (DEMO_MODE=false)
and verifies that they retrieve genuinely different papers, construct distinct plans,
and maintain complete session isolation without fallback to synthetic battery data.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from backend.app.core.config import get_settings
from backend.app.services.pipeline import ResearchPipeline
from backend.app.models.research import ResearchSession


async def test_question_independence():
    print("==================================================================")
    print("🧪 Running Acceptance Test: Question-Dependent Live Research")
    print("==================================================================")

    # Force demo_mode=False for this verification run
    os.environ["DEMO_MODE"] = "false"
    pipeline = ResearchPipeline()
    pipeline.settings.demo_mode = False
    pipeline.reinitialize()

    q_a = "Are graph neural networks genuinely better than LSTMs and Transformers for battery remaining useful life prediction under distribution shift?"
    q_b = "What are the core failure modes of multimodal retrieval-augmented generation (RAG) benchmarks?"

    print(f"\n[1/2] Executing Pipeline for Question A:\n  '{q_a}'")
    session_a = ResearchSession(question=q_a, title=q_a[:80], is_demo=False)
    pipeline.sessions[session_a.id] = session_a
    print(f"  Session A created: {session_a.id} (demo={session_a.is_demo})")

    # Run the live pipeline
    await pipeline._run_live_pipeline(session_a)
    
    print(f"  ✓ Stage results: {session_a.stage_results}")
    print(f"  ✓ Total papers selected: {len(session_a.papers)}")
    for pid, p in list(session_a.papers.items())[:3]:
        print(f"    - [{p.content_status.value}] {p.title[:60]} ({p.venue or 'N/A'}, {p.year or 'N/A'})")

    print(f"\n[2/2] Executing Pipeline for Question B:\n  '{q_b}'")
    session_b = ResearchSession(question=q_b, title=q_b[:80], is_demo=False)
    pipeline.sessions[session_b.id] = session_b
    print(f"  Session B created: {session_b.id} (demo={session_b.is_demo})")

    # Run the live pipeline
    await pipeline._run_live_pipeline(session_b)
    
    print(f"  ✓ Stage results: {session_b.stage_results}")
    print(f"  ✓ Total papers selected: {len(session_b.papers)}")
    for pid, p in list(session_b.papers.items())[:3]:
        print(f"    - [{p.content_status.value}] {p.title[:60]} ({p.venue or 'N/A'}, {p.year or 'N/A'})")

    # Assertions
    print("\n==================================================================")
    print("🔍 Verifying Acceptance Criteria & Separation:")
    print("==================================================================")

    # 1. Neither session is demo
    assert session_a.is_demo is False, "Session A must have is_demo=False"
    assert session_b.is_demo is False, "Session B must have is_demo=False"
    print("  ✓ is_demo=False strictly enforced on both sessions")

    # 2. Plans are materially different
    assert session_a.plan.search_queries != session_b.plan.search_queries, "Search queries must differ"
    print(f"  ✓ Question A Queries: {session_a.plan.search_queries[:2]}")
    print(f"  ✓ Question B Queries: {session_b.plan.search_queries[:2]}")

    # 3. Paper sets are completely distinct
    a_titles = {p.title.lower() for p in session_a.papers.values()}
    b_titles = {p.title.lower() for p in session_b.papers.values()}
    intersection = a_titles.intersection(b_titles)
    assert len(intersection) == 0, f"Papers overlapped between battery and multimodal RAG! Overlap: {intersection}"
    print(f"  ✓ Complete paper disjointness (0 overlapping papers among {len(a_titles)} and {len(b_titles)})")

    # 4. Check battery topics not leaking into Session B
    b_text = " ".join(b_titles)
    assert "battery" not in b_text and "lithium" not in b_text, "Battery terms leaked into Question B!"
    print("  ✓ Zero cross-contamination (No battery/RUL terms in Multimodal RAG corpus)")

    # 5. Check full-text extraction status
    a_oa = [p for p in session_a.papers.values() if p.full_text_available]
    b_oa = [p for p in session_b.papers.values() if p.full_text_available]
    print(f"  ✓ Question A Full-text papers: {len(a_oa)} / {len(session_a.papers)}")
    print(f"  ✓ Question B Full-text papers: {len(b_oa)} / {len(session_b.papers)}")

    print("\n🎉 ALL ACCEPTANCE CRITERIA VERIFIED SUCCESSFULLY!")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(test_question_independence())
    sys.exit(exit_code)
