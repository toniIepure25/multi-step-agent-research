"""
Reason operator — internal LLM reasoning for REE.

Uses an LLM to reason about the current epistemic state, producing
observations, analyses, or intermediate conclusions as artifacts.
"""

from __future__ import annotations

from asar.common import generate_id
from asar.core.llm import LLMClientProtocol, LLMGenerationRequest, LLMMessage, MessageRole
from schemas.ree.epistemic_event import (
    ActionType,
    EpistemicAction,
    EpistemicActionBid,
    OperatorOutcome,
    OperatorResult,
)
from schemas.ree.epistemic_state import EpistemicState, ResourceCost


class ReasonOperator:
    """Internal reasoning over the current epistemic state."""

    def __init__(self, llm_client: LLMClientProtocol, *, model: str = "default") -> None:
        self._llm = llm_client
        self._model = model

    @property
    def name(self) -> str:
        return "reason"

    async def propose(self, state: EpistemicState) -> list[EpistemicActionBid]:
        if state.budget.is_exhausted or state.process.status != "active":
            return []
        if not state.evidence_ids:
            return []

        p_success = state.views.self_model.operator_success_rates.get(
            self.name, state.views.self_model.overall_success_rate
        )

        base_gain = 0.3
        if state.views.contradiction_density > 0.0:
            base_gain += 0.2
        if state.views.highest_ignorance_priority > 0.5:
            base_gain += 0.15

        info_gain = min(1.0, base_gain * p_success)

        return [EpistemicActionBid(
            action=EpistemicAction(
                action_id=generate_id("action"),
                action_type=ActionType.REASON,
                operator_name=self.name,
                parameters={"focus": "analyze current evidence"},
                description="Reason about collected evidence to identify patterns and gaps",
            ),
            expected_information_gain=info_gain,
            probability_changes_decision=0.3 * p_success,
            novelty_gain=0.2,
            estimated_token_cost=2000,
            failure_risk=max(0.0, min(1.0, 1.0 - p_success)),
            rationale=f"Reasoning (P(success)={p_success:.2f}, contradictions={state.views.contradiction_density:.2f})",
        )]

    async def execute(self, state: EpistemicState, action: EpistemicAction) -> OperatorResult:
        evidence_summaries = []
        for eid in state.evidence_ids[:10]:
            artifact = state.artifacts.get(eid, {})
            content = artifact.get("content", "") if isinstance(artifact, dict) else ""
            if content:
                evidence_summaries.append(f"- [{eid}]: {content[:200]}")

        evidence_text = "\n".join(evidence_summaries) if evidence_summaries else "No evidence yet."

        prompt = (
            f"Goal: {state.process.goal}\n\n"
            f"Current evidence ({len(state.evidence_ids)} items):\n{evidence_text}\n\n"
            f"Analyze the evidence. Identify: (1) key findings, (2) gaps, "
            f"(3) contradictions, (4) what remains unknown."
        )

        try:
            response = await self._llm.generate(LLMGenerationRequest(
                model=self._model,
                messages=[
                    LLMMessage(role=MessageRole.SYSTEM, content="You are an analytical reasoning engine."),
                    LLMMessage(role=MessageRole.USER, content=prompt),
                ],
                temperature=0.0,
                max_tokens=1024,
                metadata={"component": "ree_reason"},
            ))
        except Exception as exc:
            return OperatorResult(
                operator_name=self.name,
                action_id=action.action_id,
                outcome=OperatorOutcome.FAILURE,
                error_message=str(exc),
                resource_cost=ResourceCost(latency_ms=100),
            )

        analysis_id = generate_id("analysis")
        return OperatorResult(
            operator_name=self.name,
            action_id=action.action_id,
            outcome=OperatorOutcome.SUCCESS,
            artifacts_produced={
                analysis_id: {
                    "type": "analysis",
                    "content": response.output_text,
                    "evidence_ids_analyzed": state.evidence_ids[:10],
                }
            },
            workspace_additions=[analysis_id],
            resource_cost=ResourceCost(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                latency_ms=500,
            ),
            notes="Analyzed evidence for patterns, gaps, and contradictions",
        )
