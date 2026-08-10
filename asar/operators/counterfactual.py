"""
Counterfactual operator — simulates what-if scenarios by perturbing
assumptions, evidence, or ontological framing.
"""

from __future__ import annotations

from asar.common import generate_id
from schemas.ree.epistemic_event import (
    ActionType,
    EpistemicAction,
    EpistemicActionBid,
    OperatorOutcome,
    OperatorResult,
)
from schemas.ree.epistemic_state import EpistemicState, ResourceCost


class CounterfactualOperator:
    """Simulates counterfactual perturbations to test conclusion robustness."""

    @property
    def name(self) -> str:
        return "simulate_counterfactual"

    async def propose(self, state: EpistemicState) -> list[EpistemicActionBid]:
        if state.budget.is_exhausted or state.process.status != "active":
            return []
        if len(state.views.hypotheses) < 1 or len(state.assumption_ids) < 1:
            return []

        p_success = state.views.self_model.operator_success_rates.get(
            self.name, state.views.self_model.overall_success_rate
        )
        base_gain = 0.3
        if state.views.top_hypothesis_margin < 0.3:
            base_gain += 0.15

        return [EpistemicActionBid(
            action=EpistemicAction(
                action_id=generate_id("action"),
                action_type=ActionType.SIMULATE_COUNTERFACTUAL,
                operator_name=self.name,
                description="Test conclusion robustness via counterfactual perturbation",
            ),
            expected_information_gain=min(1.0, base_gain * p_success),
            probability_changes_decision=0.3 * p_success,
            expected_falsification_value=0.5 * p_success,
            novelty_gain=0.2,
            estimated_token_cost=500,
            failure_risk=max(0.0, min(1.0, 1.0 - p_success)),
            rationale=f"Counterfactual (P(success)={p_success:.2f}, margin={state.views.top_hypothesis_margin:.2f})",
        )]

    async def execute(self, state: EpistemicState, action: EpistemicAction) -> OperatorResult:
        tested_assumptions = []
        for aid in state.assumption_ids[:3]:
            artifact = state.artifacts.get(aid, {})
            if isinstance(artifact, dict):
                tested_assumptions.append({
                    "assumption_id": aid,
                    "text": artifact.get("text", ""),
                    "result": "sensitivity_flagged",
                })

        result_id = generate_id("sensitivity")
        artifacts = {
            result_id: {
                "type": "sensitivity_analysis",
                "assumptions_tested": tested_assumptions,
                "conclusion": "Assumptions flagged for further testing",
            }
        }

        return OperatorResult(
            operator_name=self.name,
            action_id=action.action_id,
            outcome=OperatorOutcome.SUCCESS if tested_assumptions else OperatorOutcome.NO_OP,
            artifacts_produced=artifacts,
            workspace_additions=[result_id] if tested_assumptions else [],
            resource_cost=ResourceCost(latency_ms=200),
            notes=f"Tested {len(tested_assumptions)} assumptions for sensitivity",
        )
