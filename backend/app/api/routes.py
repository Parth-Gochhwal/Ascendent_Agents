"""NEXUS API routes."""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Query
from pydantic import BaseModel
import json

from backend.app.services.pipeline import get_pipeline
from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Request/Response Models ─────────────────────────────

class StartResearchRequest(BaseModel):
    question: str


class NoveltyRequest(BaseModel):
    idea: str


class SessionResponse(BaseModel):
    id: str
    status: str
    message: str = ""


# ─── Health ──────────────────────────────────────────────

@router.get("/health")
async def health():
    settings = get_settings()
    return {
        "status": "ok",
        "demo_mode": settings.demo_mode,
        "gemini_configured": bool(settings.gemini_api_key),
        "app": "NEXUS - AI Research Scientist"
    }


# ─── Sessions ────────────────────────────────────────────

@router.post("/research/start")
async def start_research(req: StartResearchRequest):
    if not req.question.strip():
        raise HTTPException(400, "Research question is required")
    pipeline = get_pipeline()
    session = await pipeline.start_research(req.question.strip())
    return {"id": session.id, "status": session.status.value, "message": "Research started"}


@router.get("/research/sessions")
async def list_sessions():
    pipeline = get_pipeline()
    return {"sessions": pipeline.list_sessions()}


@router.get("/research/session/{session_id}")
async def get_session(session_id: str):
    pipeline = get_pipeline()
    session = pipeline.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    session.update_stats()
    return session.model_dump(mode="json")


@router.get("/research/session/{session_id}/papers")
async def get_papers(session_id: str):
    pipeline = get_pipeline()
    session = pipeline.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    papers = list(session.papers.values())
    return {"papers": [p.model_dump(mode="json") for p in papers]}


@router.get("/research/session/{session_id}/paper/{paper_id}")
async def get_paper_detail(session_id: str, paper_id: str):
    pipeline = get_pipeline()
    session = pipeline.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    paper = session.papers.get(paper_id)
    if not paper:
        raise HTTPException(404, "Paper not found")
    analysis = session.analyses.get(paper_id)
    return {
        "paper": paper.model_dump(mode="json"),
        "analysis": analysis.model_dump(mode="json") if analysis else None
    }


@router.get("/research/session/{session_id}/claims")
async def get_claims(session_id: str):
    pipeline = get_pipeline()
    session = pipeline.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return {"claims": [c.model_dump(mode="json") for c in session.claims],
            "evidence": [e.model_dump(mode="json") for e in session.evidence]}


@router.get("/research/session/{session_id}/contradictions")
async def get_contradictions(session_id: str):
    pipeline = get_pipeline()
    session = pipeline.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return {"contradictions": [c.model_dump(mode="json") for c in session.contradictions]}


@router.get("/research/session/{session_id}/consensus")
async def get_consensus(session_id: str):
    pipeline = get_pipeline()
    session = pipeline.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return {"consensus": [c.model_dump(mode="json") for c in session.consensus]}


@router.get("/research/session/{session_id}/gaps")
async def get_gaps(session_id: str):
    pipeline = get_pipeline()
    session = pipeline.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return {"gaps": [g.model_dump(mode="json") for g in session.gaps],
            "missing_experiments": [m.model_dump(mode="json") for m in session.missing_experiments]}


@router.get("/research/session/{session_id}/novelty")
async def get_novelty(session_id: str):
    pipeline = get_pipeline()
    session = pipeline.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return {"novelty": session.novelty.model_dump(mode="json") if session.novelty else None}


@router.post("/research/session/{session_id}/novelty")
async def analyze_novelty(session_id: str, req: NoveltyRequest):
    pipeline = get_pipeline()
    result = await pipeline.analyze_novelty(session_id, req.idea)
    if not result:
        raise HTTPException(404, "Session not found or analysis failed")
    return {"novelty": result.model_dump(mode="json")}


@router.get("/research/session/{session_id}/experiment")
async def get_experiment(session_id: str):
    pipeline = get_pipeline()
    session = pipeline.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return {"experiment": session.experiment.model_dump(mode="json") if session.experiment else None}


@router.get("/research/session/{session_id}/audit")
async def get_audit(session_id: str):
    pipeline = get_pipeline()
    session = pipeline.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return {"audit": session.audit.model_dump(mode="json") if session.audit else None,
            "red_team": session.red_team.model_dump(mode="json") if session.red_team else None}


@router.get("/research/session/{session_id}/events")
async def get_events(session_id: str):
    pipeline = get_pipeline()
    session = pipeline.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return {"events": [e.model_dump(mode="json") for e in session.agent_events]}


@router.get("/research/session/{session_id}/citations")
async def get_citations(session_id: str):
    pipeline = get_pipeline()
    session = pipeline.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return {"citations": [c.model_dump(mode="json") for c in session.citations],
            "papers": {pid: {"title": p.title, "year": p.year, "id": p.id}
                       for pid, p in session.papers.items()}}


@router.get("/research/session/{session_id}/methods")
async def get_methods(session_id: str):
    pipeline = get_pipeline()
    session = pipeline.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return {"methods": [m.model_dump(mode="json") for m in session.methods]}


@router.get("/research/session/{session_id}/why")
async def get_why_explanation(
    session_id: str,
    target_type: str = Query(..., description="contradiction, consensus, gap, paper, novelty, red_team"),
    target_id: str = Query(..., description="Identifier of the target entity")
):
    """Explain WHY a specific AI-generated finding, contradiction, gap, or score was produced."""
    pipeline = get_pipeline()
    explanation = await pipeline.explain_why(session_id, target_type, target_id)
    if not explanation:
        raise HTTPException(404, "Explainability record not found for the specified target")
    return {"explanation": explanation.model_dump(mode="json")}


@router.get("/research/session/{session_id}/timeline")
async def get_research_timeline(session_id: str):
    """Get the longitudinal timeline of methods and paper milestones."""
    pipeline = get_pipeline()
    milestones = pipeline.get_timeline(session_id)
    return {"milestones": [m.model_dump(mode="json") for m in milestones]}


@router.post("/research/session/{session_id}/upload-pdf")
async def upload_pdf(session_id: str, file: UploadFile = File(...)):
    """Upload and ingest a custom scientific PDF paper into the research session."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")
    
    pipeline = get_pipeline()
    content = await file.read()
    if len(content) > 25 * 1024 * 1024:  # 25MB limit
        raise HTTPException(400, "PDF file exceeds maximum allowed size of 25MB")
    
    paper = await pipeline.ingest_pdf(session_id, content, file.filename)
    if not paper:
        raise HTTPException(500, "Failed to parse PDF text or extract sections")
    
    return {"paper": paper.model_dump(mode="json"), "message": f"Successfully ingested {file.filename}"}


@router.get("/research/session/{session_id}/bibliography")
async def get_bibliography(session_id: str, style: str = Query("apa", description="apa, ieee, or bibtex")):
    """Get structured bibliography formatted in APA, IEEE, or BibTeX."""
    pipeline = get_pipeline()
    formatted = pipeline.get_formatted_bibliography(session_id, style)
    session = pipeline.get_session(session_id)
    papers = list(session.papers.values()) if session else []
    return {
        "style": style,
        "formatted": formatted,
        "papers": [p.model_dump(mode="json") for p in papers]
    }


@router.post("/config/toggle-mode")
async def toggle_demo_mode():
    """Toggle demo/live mode."""
    settings = get_settings()
    settings.demo_mode = not settings.demo_mode
    get_pipeline().reinitialize()
    return {"demo_mode": settings.demo_mode, "message": f"Demo mode {'enabled' if settings.demo_mode else 'disabled'}"}


@router.get("/research/session/{session_id}/dossier")
async def get_dossier(session_id: str):
    """Generate the complete research dossier."""
    pipeline = get_pipeline()
    session = pipeline.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    session.update_stats()

    # Build dossier markdown
    dossier = _build_dossier(session)
    return {"dossier": dossier, "session": session.model_dump(mode="json")}


def _build_dossier(session) -> str:
    """Build markdown dossier from session data."""
    lines = []
    lines.append(f"# NEXUS Research Dossier\n")
    if session.is_demo:
        lines.append("> ⚠️ **DEMO MODE**: This dossier uses synthetic data for demonstration purposes.\n")
    lines.append(f"## 1. Executive Summary\n")
    lines.append(f"**Research Question:** {session.question}\n")
    lines.append(f"- Papers analyzed: {len(session.papers)}")
    lines.append(f"- Claims extracted: {len(session.claims)}")
    lines.append(f"- Contradictions found: {len(session.contradictions)}")
    lines.append(f"- Consensus findings: {len(session.consensus)}")
    lines.append(f"- Research gaps identified: {len(session.gaps)}\n")

    if session.plan:
        lines.append(f"## 2. Research Plan\n")
        lines.append(f"**Objective:** {session.plan.research_objective}\n")
        lines.append("**Subquestions:**")
        for sq in session.plan.subquestions:
            lines.append(f"- {sq}")
        lines.append("")

    lines.append("## 3. Literature Landscape\n")
    for p in list(session.papers.values())[:10]:
        lines.append(f"### {p.title}")
        lines.append(f"*{', '.join(a.name for a in p.authors[:3])}* ({p.year})")
        if p.venue:
            lines.append(f"*{p.venue}*")
        if p.doi:
            lines.append(f"DOI: {p.doi}")
        lines.append(f"Relevance: {p.research_score:.2f}")
        lines.append("")

    if session.contradictions:
        lines.append("## 4. Contradictions\n")
        for c in session.contradictions:
            lines.append(f"### {c.classification.value.replace('_', ' ').title()}")
            lines.append(f"**Paper A:** {c.paper_a_summary}")
            lines.append(f"> {c.claim_a_text}\n")
            lines.append(f"**Paper B:** {c.paper_b_summary}")
            lines.append(f"> {c.claim_b_text}\n")
            lines.append(f"**Explanation:** {c.explanation}\n")

    if session.consensus:
        lines.append("## 5. Consensus Findings\n")
        for c in session.consensus:
            lines.append(f"- **[{c.status.value.upper()}]** {c.statement}")
        lines.append("")

    if session.gaps:
        lines.append("## 6. Research Gaps\n")
        for g in session.gaps:
            lines.append(f"### {g.title}")
            lines.append(f"{g.description}")
            if g.potential_direction:
                lines.append(f"\n**Potential direction:** {g.potential_direction}")
            lines.append("")

    if session.experiment:
        lines.append("## 7. Experiment Proposal\n")
        lines.append(f"**Hypothesis:** {session.experiment.hypothesis}")
        lines.append(f"**Objective:** {session.experiment.research_objective}\n")

    if session.audit:
        lines.append("## 8. Research Integrity Audit\n")
        lines.append(f"- Claims checked: {session.audit.total_claims}")
        lines.append(f"- Claims with evidence: {session.audit.claims_with_evidence_links}")
        lines.append(f"- Unsupported claims: {session.audit.unsupported_claims}")
        lines.append(f"- Overall integrity: **{session.audit.overall_integrity}**\n")

    lines.append("## Bibliography\n")
    for p in session.papers.values():
        authors = ", ".join(a.name for a in p.authors[:3])
        lines.append(f"- {authors} ({p.year}). *{p.title}*. {p.venue or ''}. {'DOI: ' + p.doi if p.doi else ''}")
    lines.append("")

    lines.append("---\n*Generated by NEXUS — AI Research Scientist*")
    return "\n".join(lines)


# ─── WebSocket for live events ───────────────────────────

class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = {}

    async def connect(self, session_id: str, ws: WebSocket):
        await ws.accept()
        if session_id not in self.connections:
            self.connections[session_id] = []
        self.connections[session_id].append(ws)

    def disconnect(self, session_id: str, ws: WebSocket):
        if session_id in self.connections:
            self.connections[session_id] = [
                c for c in self.connections[session_id] if c != ws
            ]

    async def broadcast(self, session_id: str, data: dict):
        if session_id in self.connections:
            for ws in self.connections[session_id]:
                try:
                    await ws.send_json(data)
                except Exception:
                    pass


ws_manager = ConnectionManager()


@router.websocket("/ws/research/{session_id}")
async def research_websocket(websocket: WebSocket, session_id: str):
    await ws_manager.connect(session_id, websocket)
    pipeline = get_pipeline()

    # Register callback for this session
    async def event_callback(event):
        if event.session_id == session_id:
            await ws_manager.broadcast(session_id, event.model_dump(mode="json"))

    pipeline.register_callback(event_callback)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(session_id, websocket)
        pipeline.remove_callback(event_callback)
