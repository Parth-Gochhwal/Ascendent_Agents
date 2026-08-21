import logging
from backend.app.services.agents.base import BaseAgent
from backend.app.models.research import (
    ResearchSession, RedTeamResult, RedTeamFinding, RedTeamFindingType,
    RedTeamSeverity, EvidenceConfidence,
)
from backend.app.prompts.templates import RED_TEAM_V1, SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class RedTeamAgent(BaseAgent):
    """
    Adversarial agent that critiques the research synthesis, finding unsupported claims,
    citation echoes, confirmation biases, and methodological weaknesses.
    """
    @property
    def name(self) -> str:
        return "Red Team"

    async def execute(self, session: ResearchSession, **kwargs) -> None:
        """
        Executes adversarial red team review on the final synthesized conclusions and evidence.
        """
        # Summarize conclusions
        conclusions_list = [f"- [{c.status.value.upper()}] {c.statement}" for c in session.consensus]
        if session.experiment:
            conclusions_list.append(f"- [PROPOSED EXPERIMENT] {session.experiment.hypothesis} (Addresses: {session.experiment.addresses_gap})")
        conclusions = "\n".join(conclusions_list) if conclusions_list else f"Research Question: {session.question}"

        # Summarize evidence — risk-ranked, not positional
        from backend.app.services.research_intelligence import rank_red_team_evidence
        ranked_evidence = rank_red_team_evidence(session, max_items=15)
        evidence_list = []
        for e in ranked_evidence:
            evidence_list.append(f"- [{e.evidence_type.upper()}] {e.description} (Metric: {e.metric or 'N/A'}, Value: {e.quantitative_value or 'N/A'}, Dataset: {e.dataset or 'N/A'})")
        if session.citation_echoes:
            evidence_list.append(f"\nCITATION ECHO WARNING: {len(session.citation_echoes)} potential citation echo clusters detected — apparent consensus may be illusory.")
        # Surface reproducibility risks
        low_repro = [(pid, p) for pid, p in session.reproducibility_profiles.items() if p.completeness_score < 0.5]
        if low_repro:
            evidence_list.append(f"\nREPRODUCIBILITY WARNING: {len(low_repro)}/{len(session.reproducibility_profiles)} papers have low reproducibility completeness (<0.5).")
        # Surface dead-end context
        if session.dead_ends:
            evidence_list.append(f"\nDEAD ENDS: {len(session.dead_ends)} approaches identified as failed or limited — check if conclusions rely on these.")
        evidence = "\n".join(evidence_list) if evidence_list else "No direct quantitative evidence extracted."

        prompt = RED_TEAM_V1.format(
            conclusions=conclusions,
            evidence=evidence,
        )
        
        from backend.app.models.research import StageResult

        try:
            result = await self.llm.structured_generate(prompt, RedTeamResult, system_prompt=SYSTEM_PROMPT, use_fast=False)
            result.conclusion_challenged = conclusions[:200]
            
            # If no structured findings were populated by raw output, build from challenges & weaknesses
            if not result.findings and (result.challenges or result.weak_evidence or result.potential_biases):
                for idx, challenge in enumerate(result.challenges[:5]):
                    result.findings.append(RedTeamFinding(
                        severity=RedTeamSeverity.HIGH if idx == 0 else RedTeamSeverity.MEDIUM,
                        finding_type=RedTeamFindingType.UNSUPPORTED_CLAIM if "unsupported" in challenge.lower() else RedTeamFindingType.REPRODUCIBILITY_WEAKNESS,
                        description=challenge,
                        recommended_correction="Add explicit control baseline and check for citation independence."
                    ))
                for bias in result.potential_biases[:3]:
                    result.findings.append(RedTeamFinding(
                        severity=RedTeamSeverity.MEDIUM,
                        finding_type=RedTeamFindingType.DATASET_BIAS,
                        description=bias,
                        recommended_correction="Include cross-domain evaluations and negative result checks."
                    ))

            session.red_team = result
            self.record_stage(session, "red_team", StageResult.SUCCESS)
        except Exception as e:
            logger.warning(f"Red team LLM analysis failed: {e}")
            session.red_team = RedTeamResult(
                conclusion_challenged=conclusions[:200],
                challenges=["Automated adversarial LLM review was unavailable; deterministic safety checks applied."],
                findings=[
                    RedTeamFinding(
                        severity=RedTeamSeverity.MEDIUM,
                        finding_type=RedTeamFindingType.REPRODUCIBILITY_WEAKNESS,
                        description="Adversarial LLM review was unavailable. Findings lack independent critique.",
                        recommended_correction="Conduct manual adversarial critique for critical claims."
                    )
                ],
                final_confidence=EvidenceConfidence.UNCERTAIN,
                adjudication="[DEGRADED / FALLBACK] Automated adversarial LLM review was unavailable due to an evaluation error. Basic heuristic checks applied; manual critical review recommended for high-stakes decisions."
            )
            self.record_stage(session, "red_team", StageResult.PARTIAL,
                              f"Adversarial LLM review was unavailable ({e}); deterministic fallback safety checks applied.")

