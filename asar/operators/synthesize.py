"""
Synthesize operator — produces claims from collected evidence for REE.

Wraps the existing deliberation capability, adapting it to the
operator protocol with typed OperatorResult output.
"""

from __future__ import annotations

import json

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


class SynthesizeOperator:
    """Synthesizes evidence into claims."""

    def __init__(self, llm_client: LLMClientProtocol, *, model: str = "default") -> None:
        self._llm = llm_client
        self._model = model

    @property
    def name(self) -> str:
        return "synthesize"

    async def propose(self, state: EpistemicState) -> list[EpistemicActionBid]:
        if state.budget.is_exhausted or state.process.status != "active":
            return []
        if len(state.evidence_ids) < 2:
            return []
        already_synthesized = "synthesize" in state.operator_history

        return [EpistemicActionBid(
            action=EpistemicAction(
                action_id=generate_id("action"),
                action_type=ActionType.SYNTHESIZE,
                operator_name=self.name,
                parameters={},
                description="Synthesize collected evidence into structured claims",
            ),
            expected_information_gain=0.4 if not already_synthesized else 0.2,
            probability_changes_decision=0.6 if not already_synthesized else 0.3,
            novelty_gain=0.3,
            estimated_token_cost=3000,
            rationale="Produce structured claims from accumulated evidence",
        )]

    async def execute(self, state: EpistemicState, action: EpistemicAction) -> OperatorResult:
        evidence_items = []
        for eid in state.evidence_ids:
            artifact = state.artifacts.get(eid, {})
            if isinstance(artifact, dict) and "content" in artifact:
                evidence_items.append({
                    "evidence_id": eid,
                    "content": artifact["content"][:300],
                })

        prompt = (
            f"Goal: {state.process.goal}\n\n"
            f"Evidence:\n{json.dumps(evidence_items, indent=2)}\n\n"
            f"Produce a JSON object with:\n"
            f'- "claims": list of objects with "text", "supporting_evidence_ids", '
            f'"epistemic_status" (high_confidence/moderate_confidence/low_confidence)\n'
            f'- "synthesis": a brief overall synthesis\n'
            f'- "information_gaps": list of strings describing what is missing'
        )

        try:
            response = await self._llm.generate(LLMGenerationRequest(
                model=self._model,
                messages=[
                    LLMMessage(role=MessageRole.SYSTEM, content="You are a research synthesis engine. Output valid JSON only."),
                    LLMMessage(role=MessageRole.USER, content=prompt),
                ],
                temperature=0.0,
                max_tokens=2048,
                metadata={"component": "ree_synthesize"},
            ))
        except Exception as exc:
            return OperatorResult(
                operator_name=self.name,
                action_id=action.action_id,
                outcome=OperatorOutcome.FAILURE,
                error_message=str(exc),
                resource_cost=ResourceCost(latency_ms=100),
            )

        try:
            parsed = json.loads(response.output_text)
        except json.JSONDecodeError:
            parsed = {"claims": [], "synthesis": response.output_text, "information_gaps": []}

        artifacts: dict[str, object] = {}
        workspace_additions: list[str] = []

        for claim_data in parsed.get("claims", []):
            cid = generate_id("claim")
            artifacts[cid] = {
                "type": "claim",
                "text": claim_data.get("text", ""),
                "supporting_evidence_ids": claim_data.get("supporting_evidence_ids", []),
                "epistemic_status": claim_data.get("epistemic_status", "moderate_confidence"),
            }
            workspace_additions.append(cid)

        synthesis_id = generate_id("synthesis")
        artifacts[synthesis_id] = {
            "type": "synthesis",
            "content": parsed.get("synthesis", ""),
            "information_gaps": parsed.get("information_gaps", []),
        }

        return OperatorResult(
            operator_name=self.name,
            action_id=action.action_id,
            outcome=OperatorOutcome.SUCCESS if artifacts else OperatorOutcome.NO_OP,
            artifacts_produced=artifacts,
            workspace_additions=workspace_additions,
            resource_cost=ResourceCost(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                latency_ms=800,
            ),
            notes=f"Produced {len(parsed.get('claims', []))} claims from {len(evidence_items)} evidence items",
        )
