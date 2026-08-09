"""
Hypothesis operators — generate, attack, and manage hypotheses.

Implements the abduction-deduction-testing cycle:
observation -> abduction -> candidate explanation -> deduced predictions
-> potential discriminating evidence -> observation -> belief revision
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


class GenerateHypothesisOperator:
    """Generates candidate hypotheses via abduction from evidence."""

    def __init__(self, llm_client: LLMClientProtocol, *, model: str = "default") -> None:
        self._llm = llm_client
        self._model = model

    @property
    def name(self) -> str:
        return "generate_hypothesis"

    async def propose(self, state: EpistemicState) -> list[EpistemicActionBid]:
        if state.budget.is_exhausted or state.process.status != "active":
            return []
        if not state.evidence_ids:
            return []
        existing_count = len(state.hypothesis_ids)
        if existing_count >= 10:
            return []

        gain = 0.7 if existing_count < 2 else 0.4
        return [EpistemicActionBid(
            action=EpistemicAction(
                action_id=generate_id("action"),
                action_type=ActionType.GENERATE_HYPOTHESIS,
                operator_name=self.name,
                parameters={"diversity_target": max(3, existing_count + 2)},
                description="Generate diverse candidate hypotheses from evidence",
            ),
            expected_information_gain=gain,
            probability_changes_decision=0.5,
            novelty_gain=0.6 if existing_count < 3 else 0.3,
            estimated_token_cost=2500,
            rationale="Abductive reasoning to generate candidate explanations",
        )]

    async def execute(self, state: EpistemicState, action: EpistemicAction) -> OperatorResult:
        evidence_summaries = []
        for eid in state.evidence_ids[:8]:
            artifact = state.artifacts.get(eid, {})
            content = artifact.get("content", "") if isinstance(artifact, dict) else ""
            if content:
                evidence_summaries.append(f"- [{eid}]: {content[:200]}")

        existing_hyps = []
        for hid in state.hypothesis_ids:
            artifact = state.artifacts.get(hid, {})
            if isinstance(artifact, dict):
                existing_hyps.append(artifact.get("statement", ""))

        existing_text = "\n".join(f"- {h}" for h in existing_hyps) if existing_hyps else "None yet."

        prompt = (
            f"Goal: {state.process.goal}\n\n"
            f"Evidence:\n{''.join(evidence_summaries)}\n\n"
            f"Existing hypotheses:\n{existing_text}\n\n"
            f"Generate 2-4 structurally different candidate hypotheses.\n"
            f"For EACH hypothesis include:\n"
            f'- "statement": the hypothesis\n'
            f'- "ontology_frame": conceptual frame (e.g. causal, statistical, institutional)\n'
            f'- "prior": initial plausibility [0-1]\n'
            f'- "predictions": list of testable predictions\n'
            f'- "falsifiers": observations that would weaken this hypothesis\n'
            f'- "assumptions": key assumptions\n'
            f'- "generation_method": how you generated this (e.g. abduction, analogy)\n\n'
            f"Optimize for USEFUL DIVERSITY, not paraphrases.\n"
            f"Output a JSON list of hypothesis objects."
        )

        try:
            response = await self._llm.generate(LLMGenerationRequest(
                model=self._model,
                messages=[
                    LLMMessage(role=MessageRole.SYSTEM, content="You are a hypothesis generation engine. Output valid JSON only."),
                    LLMMessage(role=MessageRole.USER, content=prompt),
                ],
                temperature=0.7,
                max_tokens=2048,
                metadata={"component": "ree_generate_hypothesis"},
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
            if isinstance(parsed, dict) and "hypotheses" in parsed:
                parsed = parsed["hypotheses"]
            if not isinstance(parsed, list):
                parsed = [parsed]
        except json.JSONDecodeError:
            parsed = []

        artifacts: dict[str, object] = {}
        workspace_additions: list[str] = []

        for hyp_data in parsed:
            if not isinstance(hyp_data, dict):
                continue
            hid = generate_id("hypothesis")
            artifacts[hid] = {
                "type": "hypothesis",
                "hypothesis_id": hid,
                "statement": hyp_data.get("statement", ""),
                "ontology_frame": hyp_data.get("ontology_frame", "default"),
                "prior": max(0.0, min(1.0, float(hyp_data.get("prior", 0.5)))),
                "posterior": max(0.0, min(1.0, float(hyp_data.get("prior", 0.5)))),
                "status": "proposed",
                "generation_method": hyp_data.get("generation_method", "abduction"),
                "assumptions": hyp_data.get("assumptions", []),
                "predictions": hyp_data.get("predictions", []),
                "falsifiers": hyp_data.get("falsifiers", []),
            }
            workspace_additions.append(hid)

            for i, pred_text in enumerate(hyp_data.get("predictions", [])):
                if isinstance(pred_text, str):
                    pid = generate_id("prediction")
                    artifacts[pid] = {
                        "type": "prediction",
                        "prediction_id": pid,
                        "hypothesis_id": hid,
                        "statement": pred_text,
                    }

            for i, fals_text in enumerate(hyp_data.get("falsifiers", [])):
                if isinstance(fals_text, str):
                    fid = generate_id("falsifier")
                    artifacts[fid] = {
                        "type": "falsifier",
                        "falsifier_id": fid,
                        "hypothesis_id": hid,
                        "statement": fals_text,
                    }

            for i, assum_text in enumerate(hyp_data.get("assumptions", [])):
                if isinstance(assum_text, str):
                    aid = generate_id("assumption")
                    artifacts[aid] = {
                        "type": "assumption",
                        "assumption_id": aid,
                        "text": assum_text,
                        "dependent_hypothesis_ids": [hid],
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
                latency_ms=600,
            ),
            notes=f"Generated {len(workspace_additions)} hypotheses with predictions and falsifiers",
        )


class AttackHypothesisOperator:
    """Attempts to find weaknesses in existing hypotheses."""

    def __init__(self, llm_client: LLMClientProtocol, *, model: str = "default") -> None:
        self._llm = llm_client
        self._model = model

    @property
    def name(self) -> str:
        return "attack_hypothesis"

    async def propose(self, state: EpistemicState) -> list[EpistemicActionBid]:
        if state.budget.is_exhausted or state.process.status != "active":
            return []
        if len(state.hypothesis_ids) < 1:
            return []

        return [EpistemicActionBid(
            action=EpistemicAction(
                action_id=generate_id("action"),
                action_type=ActionType.ATTACK_HYPOTHESIS,
                operator_name=self.name,
                parameters={},
                description="Attack existing hypotheses to test their robustness",
            ),
            expected_information_gain=0.4,
            expected_falsification_value=0.7,
            probability_changes_decision=0.4,
            estimated_token_cost=2000,
            rationale="Falsification-oriented analysis of existing hypotheses",
        )]

    async def execute(self, state: EpistemicState, action: EpistemicAction) -> OperatorResult:
        hyp_summaries = []
        for hid in state.hypothesis_ids[:5]:
            artifact = state.artifacts.get(hid, {})
            if isinstance(artifact, dict):
                hyp_summaries.append(f"- [{hid}]: {artifact.get('statement', '')}")

        prompt = (
            f"Goal: {state.process.goal}\n\n"
            f"Active hypotheses:\n{''.join(hyp_summaries)}\n\n"
            f"For each hypothesis, identify:\n"
            f'1. Weaknesses and potential counterarguments\n'
            f'2. Untested assumptions\n'
            f'3. Potential contradictions with evidence\n'
            f'4. What would need to be true for this to be wrong\n\n'
            f"Output JSON with a list of attack objects, each having:\n"
            f'"hypothesis_id", "weaknesses" (list), "contradictions" (list), '
            f'"ignorance_items" (list of things we should check)'
        )

        try:
            response = await self._llm.generate(LLMGenerationRequest(
                model=self._model,
                messages=[
                    LLMMessage(role=MessageRole.SYSTEM, content="You are a critical analysis engine. Output valid JSON only."),
                    LLMMessage(role=MessageRole.USER, content=prompt),
                ],
                temperature=0.3,
                max_tokens=1500,
                metadata={"component": "ree_attack_hypothesis"},
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
            if not isinstance(parsed, list):
                parsed = parsed.get("attacks", [parsed])
        except json.JSONDecodeError:
            parsed = []

        artifacts: dict[str, object] = {}
        for attack in parsed:
            if not isinstance(attack, dict):
                continue
            for ign_text in attack.get("ignorance_items", []):
                if isinstance(ign_text, str):
                    iid = generate_id("ignorance")
                    artifacts[iid] = {
                        "type": "ignorance_item",
                        "ignorance_id": iid,
                        "ignorance_type": "untested_assumption",
                        "description": ign_text,
                        "related_hypothesis_ids": [attack.get("hypothesis_id", "")],
                    }

        return OperatorResult(
            operator_name=self.name,
            action_id=action.action_id,
            outcome=OperatorOutcome.SUCCESS,
            artifacts_produced=artifacts,
            resource_cost=ResourceCost(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                latency_ms=500,
            ),
            notes=f"Attacked hypotheses; produced {len(artifacts)} ignorance items",
        )
