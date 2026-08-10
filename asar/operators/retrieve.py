"""
Retrieve operator — wraps the existing execution layer for REE.

Proposes evidence retrieval actions and executes them via a search client,
producing EvidenceItems as artifacts.
"""

from __future__ import annotations

from asar.common import IDPrefix, generate_id
from asar.core.search import SearchClientProtocol, SearchRequest
from schemas.evidence_item import EvidenceItem, SourceMetadata, SourceType
from schemas.ree.epistemic_event import (
    ActionType,
    EpistemicAction,
    EpistemicActionBid,
    OperatorOutcome,
    OperatorResult,
)
from schemas.ree.epistemic_state import EpistemicState, ResourceCost


class RetrieveOperator:
    """Retrieves evidence from external sources."""

    def __init__(self, search_client: SearchClientProtocol, *, top_k: int = 5) -> None:
        self._search = search_client
        self._top_k = top_k

    @property
    def name(self) -> str:
        return "retrieve"

    async def propose(self, state: EpistemicState) -> list[EpistemicActionBid]:
        if state.budget.is_exhausted:
            return []
        if state.process.status != "active":
            return []

        base_gain = 0.6 if len(state.evidence_ids) < 5 else 0.3

        ignorance_boost = 0.0
        for iv in state.views.ignorance_items.values():
            if iv.status == "open" and iv.ignorance_type in ("missing_evidence", "unknown", "untested_assumption"):
                ignorance_boost = max(ignorance_boost, iv.priority * 0.3)

        p_success = state.views.self_model.operator_success_rates.get(
            self.name, state.views.self_model.overall_success_rate
        )
        info_gain = min(1.0, (base_gain + ignorance_boost) * p_success)

        return [EpistemicActionBid(
            action=EpistemicAction(
                action_id=generate_id("action"),
                action_type=ActionType.RETRIEVE,
                operator_name=self.name,
                parameters={"query": state.process.goal, "top_k": self._top_k},
                description=f"Search for evidence about: {state.process.goal}",
            ),
            expected_information_gain=info_gain,
            probability_changes_decision=0.4 * p_success,
            novelty_gain=0.5 if len(state.evidence_ids) < 3 else 0.2,
            estimated_token_cost=500,
            failure_risk=max(0.0, min(1.0, 1.0 - p_success)),
            rationale=f"Retrieve evidence (P(success)={p_success:.2f}, ign_boost={ignorance_boost:.2f})",
        )]

    async def execute(self, state: EpistemicState, action: EpistemicAction) -> OperatorResult:
        query = action.parameters.get("query", state.process.goal)
        top_k = action.parameters.get("top_k", self._top_k)

        try:
            response = await self._search.search(SearchRequest(query=query, top_k=top_k))
        except Exception as exc:
            return OperatorResult(
                operator_name=self.name,
                action_id=action.action_id,
                outcome=OperatorOutcome.FAILURE,
                error_message=str(exc),
                resource_cost=ResourceCost(latency_ms=100),
            )

        artifacts: dict[str, object] = {}
        workspace_additions: list[str] = []

        for result_item in response.results:
            eid = generate_id(IDPrefix.EVIDENCE)
            evidence = EvidenceItem(
                evidence_id=eid,
                task_id=action.action_id,
                content=result_item.snippet,
                source=SourceMetadata(
                    source_type=SourceType.WEB_SEARCH,
                    url=result_item.url,
                    title=result_item.title,
                    raw_snippet=result_item.snippet,
                ),
                confidence=result_item.score or 0.5,
                relevance=0.5,
            )
            artifacts[eid] = evidence.model_dump()
            workspace_additions.append(eid)

        return OperatorResult(
            operator_name=self.name,
            action_id=action.action_id,
            outcome=OperatorOutcome.SUCCESS if artifacts else OperatorOutcome.NO_OP,
            artifacts_produced=artifacts,
            workspace_additions=workspace_additions,
            resource_cost=ResourceCost(latency_ms=200),
            notes=f"Retrieved {len(artifacts)} evidence items",
        )
