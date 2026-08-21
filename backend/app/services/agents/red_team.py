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

        # Summarize evidence
        evidence_list = []
        for e in session.evidence[:15]:
            evidence_list.append(f"- [{e.evidence_type.upper()}] {e.description} (Metric: {e.metric or 'N/A'}, Value: {e.quantitative_value or 'N/A'}, Dataset: {e.dataset or 'N/A'})")
        if session.citation_echoes:
            evidence_list.append(f"\nNOTE: {len(session.citation_echoes)} potential citation echo clusters detected in corpus.")
        evidence = "\n".join(evidence_list) if evidence_list else "No direct quantitative evidence extracted."

        prompt = RED_TEAM_V1.format(
            conclusions=conclusions,
            evidence=evidence,
        )
        
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
        except Exception as e:
            logger.warning(f"Red team analysis failed: {e}")
            session.red_team = RedTeamResult(
                conclusion_challenged=conclusions[:200],
                challenges=["Automated red team review encountered an evaluation limit."],
                final_confidence=EvidenceConfidence.MEDIUM,
                adjudication="Manual critical review recommended for high-stakes decisions."
            )

