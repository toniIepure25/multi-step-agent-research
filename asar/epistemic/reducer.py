"""
State reducer — the ONLY component that produces new EpistemicState instances.

Projects epistemic events into:
  1. Artifact ID lists (evidence, claims, hypotheses, etc.)
  2. Materialized views (HypothesisView, IgnoranceView, BeliefSnapshot)
  3. Derived features (hypothesis_entropy, workspace_saturation, etc.)

Replay through events from an initial state MUST reconstruct equivalent
rich state including all materialized views — not merely artifact IDs.
"""

from __future__ import annotations

from schemas.ree.epistemic_event import EpistemicEvent, OperatorOutcome
from schemas.ree.epistemic_state import (
    BeliefSnapshot,
    BudgetState,
    EpistemicState,
    HypothesisView,
    IgnoranceView,
    MaterializedViews,
    ResourceCost,
    WorkspaceSlot,
    WorkspaceState,
)


class StateReducer:
    """Applies EpistemicEvents to produce new immutable EpistemicState instances.

    This is the authoritative event → epistemic-view projection layer.
    No other component may write to materialized views.
    """

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

        new_hypotheses = dict(state.views.hypotheses)
        new_belief_trajectory = list(state.views.belief_trajectory)
        new_ignorance_views = dict(state.views.ignorance_items)

        for artifact_id, artifact in result.artifacts_produced.items():
            new_artifacts[artifact_id] = artifact
            self._classify_artifact(
                artifact_id, artifact,
                new_evidence_ids, new_claim_ids, new_hypothesis_ids,
                new_assumption_ids, new_ignorance_ids, new_contradiction_ids,
            )
            self._project_hypothesis(
                artifact_id, artifact, new_version,
                new_hypotheses, new_belief_trajectory,
            )
            self._project_ignorance(artifact_id, artifact, new_ignorance_views)
            self._link_supporting_evidence(artifact_id, artifact, new_hypotheses)

        for artifact_id, artifact in result.artifacts_modified.items():
            new_artifacts[artifact_id] = artifact
            self._project_hypothesis(
                artifact_id, artifact, new_version,
                new_hypotheses, new_belief_trajectory,
            )
            self._project_ignorance(artifact_id, artifact, new_ignorance_views)

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

        new_views = MaterializedViews(
            hypotheses=new_hypotheses,
            belief_trajectory=new_belief_trajectory,
            ignorance_items=new_ignorance_views,
            self_model=state.views.self_model,
            decision_stability=state.views.decision_stability,
        ).compute_derived(
            workspace=new_workspace,
            contradiction_count=len(new_contradiction_ids),
            evidence_count=len(new_evidence_ids),
        )

        return EpistemicState(
            version=new_version,
            process=new_process,
            budget=new_budget,
            workspace=new_workspace,
            views=new_views,
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
        """Replay a sequence of events from an initial state.

        Reconstructs equivalent rich state including all materialized views.
        """
        state = initial_state
        for event in events:
            state = self.apply(state, event)
        return state

    # ------------------------------------------------------------------
    # View projection methods
    # ------------------------------------------------------------------

    def _project_hypothesis(
        self,
        artifact_id: str,
        artifact: object,
        version: int,
        hypotheses: dict[str, HypothesisView],
        trajectory: list[BeliefSnapshot],
    ) -> None:
        """Project a hypothesis artifact into the HypothesisView + trajectory."""
        if not artifact_id.startswith("hypothesis_"):
            return
        if not isinstance(artifact, dict):
            return

        existing = hypotheses.get(artifact_id)
        prior_posterior = existing.posterior if existing else 0.5

        view = HypothesisView(
            hypothesis_id=artifact_id,
            statement=artifact.get("statement", existing.statement if existing else ""),
            ontology_frame=artifact.get("ontology_frame", existing.ontology_frame if existing else "default"),
            prior=float(artifact.get("prior", existing.prior if existing else 0.5)),
            posterior=max(0.0, min(1.0, float(artifact.get("posterior", prior_posterior)))),
            status=artifact.get("status", existing.status if existing else "proposed"),
            supporting_evidence_ids=list(existing.supporting_evidence_ids) if existing else [],
            attacking_evidence_ids=list(existing.attacking_evidence_ids) if existing else [],
            assumption_ids=artifact.get("assumptions", existing.assumption_ids if existing else [])
                           if isinstance(artifact.get("assumptions"), list) and all(isinstance(a, str) for a in artifact.get("assumptions", []))
                           else (existing.assumption_ids if existing else []),
            prediction_ids=list(existing.prediction_ids) if existing else [],
            falsifier_ids=list(existing.falsifier_ids) if existing else [],
            generation_method=artifact.get("generation_method", existing.generation_method if existing else ""),
        )
        hypotheses[artifact_id] = view

        trajectory.append(BeliefSnapshot(
            hypothesis_id=artifact_id,
            version=version,
            posterior=view.posterior,
            status=view.status,
        ))

    def _project_ignorance(
        self,
        artifact_id: str,
        artifact: object,
        ignorance_views: dict[str, IgnoranceView],
    ) -> None:
        """Project an ignorance artifact into the IgnoranceView."""
        if not artifact_id.startswith("ignorance_"):
            return
        if not isinstance(artifact, dict):
            return

        impact = float(artifact.get("impact_if_resolved", 0.5))
        resolvability = float(artifact.get("resolvability", 0.5))
        decision_relevant = float(artifact.get("probability_decision_relevant", 0.5))
        priority = decision_relevant * impact * resolvability

        related = artifact.get("related_hypothesis_ids", [])
        if not isinstance(related, list):
            related = []

        ignorance_views[artifact_id] = IgnoranceView(
            ignorance_id=artifact_id,
            ignorance_type=artifact.get("ignorance_type", "unknown"),
            description=artifact.get("description", ""),
            priority=priority,
            status=artifact.get("status", "open"),
            related_hypothesis_ids=related,
            impact_if_resolved=impact,
            resolvability=resolvability,
        )

    def _link_supporting_evidence(
        self,
        artifact_id: str,
        artifact: object,
        hypotheses: dict[str, HypothesisView],
    ) -> None:
        """Link evidence/claim artifacts to their supporting hypotheses."""
        if not isinstance(artifact, dict):
            return

        if artifact_id.startswith("claim_"):
            for eid in artifact.get("supporting_evidence_ids", []):
                if isinstance(eid, str) and eid.startswith("hypothesis_") and eid in hypotheses:
                    h = hypotheses[eid]
                    if artifact_id not in h.supporting_evidence_ids:
                        hypotheses[eid] = h.model_copy(update={
                            "supporting_evidence_ids": [*h.supporting_evidence_ids, artifact_id],
                        })

        if artifact_id.startswith("prediction_") or artifact_id.startswith("falsifier_"):
            hyp_id = artifact.get("hypothesis_id", "")
            if hyp_id and hyp_id in hypotheses:
                h = hypotheses[hyp_id]
                if artifact_id.startswith("prediction_") and artifact_id not in h.prediction_ids:
                    hypotheses[hyp_id] = h.model_copy(update={
                        "prediction_ids": [*h.prediction_ids, artifact_id],
                    })
                elif artifact_id.startswith("falsifier_") and artifact_id not in h.falsifier_ids:
                    hypotheses[hyp_id] = h.model_copy(update={
                        "falsifier_ids": [*h.falsifier_ids, artifact_id],
                    })

        if artifact_id.startswith("assumption_"):
            for hyp_id in artifact.get("dependent_hypothesis_ids", []):
                if isinstance(hyp_id, str) and hyp_id in hypotheses:
                    h = hypotheses[hyp_id]
                    if artifact_id not in h.assumption_ids:
                        hypotheses[hyp_id] = h.model_copy(update={
                            "assumption_ids": [*h.assumption_ids, artifact_id],
                        })

    # ------------------------------------------------------------------
    # Existing projection methods
    # ------------------------------------------------------------------

    def _update_budget(self, budget: BudgetState, cost: ResourceCost) -> BudgetState:
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
