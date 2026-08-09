"""
State reducer — applies epistemic events to produce new immutable states.

The reducer is the ONLY component that produces new EpistemicState instances.
Operators return OperatorResults; the reducer applies them.
"""

from __future__ import annotations

from schemas.ree.epistemic_event import EpistemicEvent, OperatorOutcome
from schemas.ree.epistemic_state import (
    BudgetState,
    EpistemicState,
    WorkspaceSlot,
    WorkspaceState,
)


class StateReducer:
    """Applies EpistemicEvents to produce new immutable EpistemicState instances."""

    def apply(self, state: EpistemicState, event: EpistemicEvent) -> EpistemicState:
        """Apply an event to the current state and return a new state."""
        result = event.result
        new_version = state.version + 1

        new_artifacts = dict(state.artifacts)
        new_evidence_ids = list(state.evidence_ids)
        new_claim_ids = list(state.claim_ids)
        new_hypothesis_ids = list(state.hypothesis_ids)
        new_assumption_ids = list(state.assumption_ids)
        new_ignorance_ids = list(state.ignorance_ids)
        new_contradiction_ids = list(state.contradiction_ids)

        for artifact_id, artifact in result.artifacts_produced.items():
            new_artifacts[artifact_id] = artifact
            self._classify_artifact(
                artifact_id, artifact,
                new_evidence_ids, new_claim_ids, new_hypothesis_ids,
                new_assumption_ids, new_ignorance_ids, new_contradiction_ids,
            )

        for artifact_id, artifact in result.artifacts_modified.items():
            new_artifacts[artifact_id] = artifact

        new_budget = self._update_budget(state.budget, event.resource_cost)
        new_workspace = self._update_workspace(
            state.workspace, result, new_version
        )
        new_operator_history = [*state.operator_history, result.operator_name]

        new_process = state.process.model_copy(
            update={"step_count": state.process.step_count + 1}
        )

        if event.action.action_type.value == "stop":
            new_process = new_process.model_copy(
                update={
                    "status": "completed",
                    "stop_reason": result.notes or "stop action selected",
                }
            )
        elif event.action.action_type.value == "abstain":
            new_process = new_process.model_copy(
                update={
                    "status": "abstained",
                    "stop_reason": result.notes or "abstain action selected",
                }
            )

        return EpistemicState(
            version=new_version,
            process=new_process,
            budget=new_budget,
            workspace=new_workspace,
            evidence_ids=new_evidence_ids,
            claim_ids=new_claim_ids,
            hypothesis_ids=new_hypothesis_ids,
            assumption_ids=new_assumption_ids,
            ignorance_ids=new_ignorance_ids,
            contradiction_ids=new_contradiction_ids,
            artifacts=new_artifacts,
            operator_history=new_operator_history,
        )

    def replay(self, initial_state: EpistemicState, events: list[EpistemicEvent]) -> EpistemicState:
        """Replay a sequence of events from an initial state."""
        state = initial_state
        for event in events:
            state = self.apply(state, event)
        return state

    def _update_budget(self, budget: BudgetState, cost: "ResourceCost") -> BudgetState:
        from schemas.ree.epistemic_state import ResourceCost as RC
        return budget.model_copy(update={
            "tokens_used": budget.tokens_used + cost.total_tokens,
            "steps_used": budget.steps_used + 1,
            "cost_used_usd": budget.cost_used_usd + cost.api_cost_usd,
            "latency_used_ms": budget.latency_used_ms + cost.latency_ms,
        })

    def _update_workspace(
        self,
        workspace: WorkspaceState,
        result: "OperatorResult",
        version: int,
    ) -> WorkspaceState:
        from schemas.ree.epistemic_event import OperatorResult as OR
        slots = [s for s in workspace.slots if s.artifact_id not in result.workspace_removals]

        for artifact_id in result.workspace_additions:
            if len(slots) >= workspace.capacity:
                slots.sort(key=lambda s: s.salience)
                if slots and slots[0].salience < 0.5:
                    slots.pop(0)
                elif len(slots) >= workspace.capacity:
                    continue

            slots.append(WorkspaceSlot(
                artifact_id=artifact_id,
                artifact_type=result.operator_name,
                salience=0.5,
                added_at_version=version,
            ))

        return workspace.model_copy(update={"slots": slots})

    def _classify_artifact(
        self,
        artifact_id: str,
        artifact: object,
        evidence_ids: list[str],
        claim_ids: list[str],
        hypothesis_ids: list[str],
        assumption_ids: list[str],
        ignorance_ids: list[str],
        contradiction_ids: list[str],
    ) -> None:
        """Classify an artifact by its ID prefix into the appropriate list."""
        if artifact_id.startswith("evidence_"):
            if artifact_id not in evidence_ids:
                evidence_ids.append(artifact_id)
        elif artifact_id.startswith("claim_"):
            if artifact_id not in claim_ids:
                claim_ids.append(artifact_id)
        elif artifact_id.startswith("hypothesis_"):
            if artifact_id not in hypothesis_ids:
                hypothesis_ids.append(artifact_id)
        elif artifact_id.startswith("assumption_"):
            if artifact_id not in assumption_ids:
                assumption_ids.append(artifact_id)
        elif artifact_id.startswith("ignorance_"):
            if artifact_id not in ignorance_ids:
                ignorance_ids.append(artifact_id)
        elif artifact_id.startswith("contradiction_"):
            if artifact_id not in contradiction_ids:
                contradiction_ids.append(artifact_id)
