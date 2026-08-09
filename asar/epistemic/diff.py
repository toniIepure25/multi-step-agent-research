"""
State diffing — compare two EpistemicState instances and produce a typed diff.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from schemas.ree.epistemic_state import EpistemicState


@dataclass(frozen=True)
class StateDiff:
    """Typed diff between two EpistemicState versions."""

    version_from: int
    version_to: int
    new_evidence_ids: list[str] = field(default_factory=list)
    new_claim_ids: list[str] = field(default_factory=list)
    new_hypothesis_ids: list[str] = field(default_factory=list)
    new_assumption_ids: list[str] = field(default_factory=list)
    new_ignorance_ids: list[str] = field(default_factory=list)
    new_contradiction_ids: list[str] = field(default_factory=list)
    removed_workspace_ids: list[str] = field(default_factory=list)
    added_workspace_ids: list[str] = field(default_factory=list)
    budget_tokens_consumed: int = 0
    budget_steps_consumed: int = 0
    operators_invoked: list[str] = field(default_factory=list)
    status_changed: bool = False


def compute_diff(before: EpistemicState, after: EpistemicState) -> StateDiff:
    """Compute the typed diff between two states."""
    before_ws = {s.artifact_id for s in before.workspace.slots}
    after_ws = {s.artifact_id for s in after.workspace.slots}

    return StateDiff(
        version_from=before.version,
        version_to=after.version,
        new_evidence_ids=[i for i in after.evidence_ids if i not in before.evidence_ids],
        new_claim_ids=[i for i in after.claim_ids if i not in before.claim_ids],
        new_hypothesis_ids=[i for i in after.hypothesis_ids if i not in before.hypothesis_ids],
        new_assumption_ids=[i for i in after.assumption_ids if i not in before.assumption_ids],
        new_ignorance_ids=[i for i in after.ignorance_ids if i not in before.ignorance_ids],
        new_contradiction_ids=[i for i in after.contradiction_ids if i not in before.contradiction_ids],
        removed_workspace_ids=sorted(before_ws - after_ws),
        added_workspace_ids=sorted(after_ws - before_ws),
        budget_tokens_consumed=after.budget.tokens_used - before.budget.tokens_used,
        budget_steps_consumed=after.budget.steps_used - before.budget.steps_used,
        operators_invoked=after.operator_history[len(before.operator_history):],
        status_changed=before.process.status != after.process.status,
    )
