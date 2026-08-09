"""
Tests for federated memory: stores, consolidation, provenance, lifecycle.
"""

from __future__ import annotations

import pytest

from asar.memory_federation.federation import FederatedMemory
from asar.memory_federation.consolidation import MemoryConsolidator
from schemas.ree.memory import MemoryRecordStatus, MemoryStore


class TestFederatedMemory:
    def test_store_and_retrieve(self) -> None:
        mem = FederatedMemory()
        record = mem.store(MemoryStore.WORKING, "test content")
        assert record.store == MemoryStore.WORKING
        retrieved = mem.retrieve(MemoryStore.WORKING)
        assert len(retrieved) == 1

    def test_store_across_multiple_stores(self) -> None:
        mem = FederatedMemory()
        mem.store(MemoryStore.WORKING, "working item")
        mem.store(MemoryStore.EPISODIC, "episode item")
        mem.store(MemoryStore.SEMANTIC, "belief item")
        mem.store(MemoryStore.PROCEDURAL, "strategy item")
        mem.store(MemoryStore.SELF_MODEL, "capability item")
        mem.store(MemoryStore.PROSPECTIVE, "future check")
        mem.store(MemoryStore.IGNORANCE, "unknown item")

        counts = mem.store_counts()
        assert counts["working"] == 1
        assert counts["episodic"] == 1
        assert counts["semantic"] == 1
        assert counts["procedural"] == 1
        assert counts["self_model"] == 1
        assert counts["prospective"] == 1
        assert counts["ignorance"] == 1

    def test_retrieve_with_filters(self) -> None:
        mem = FederatedMemory()
        mem.store(MemoryStore.SEMANTIC, "high", salience=0.9, tags=["important"])
        mem.store(MemoryStore.SEMANTIC, "low", salience=0.1, tags=["trivial"])
        results = mem.retrieve(MemoryStore.SEMANTIC, min_salience=0.5)
        assert len(results) == 1
        assert results[0].content == "high"

    def test_retrieve_with_tags(self) -> None:
        mem = FederatedMemory()
        mem.store(MemoryStore.EPISODIC, "tagged", tags=["finance"])
        mem.store(MemoryStore.EPISODIC, "other", tags=["science"])
        results = mem.retrieve(MemoryStore.EPISODIC, tags=["finance"])
        assert len(results) == 1

    def test_access_updates_count(self) -> None:
        mem = FederatedMemory()
        record = mem.store(MemoryStore.WORKING, "content")
        assert record.access_count == 0
        accessed = mem.access(record.record_id)
        assert accessed.access_count == 1

    def test_update_content_reconsolidation(self) -> None:
        mem = FederatedMemory()
        record = mem.store(MemoryStore.SEMANTIC, "old belief")
        updated = mem.update_content(record.record_id, "new belief", "correction")
        assert updated.content == "new belief"
        assert updated.version == 2
        assert updated.status == MemoryRecordStatus.RECONSOLIDATED
        assert len(mem.version_history(record.record_id)) == 1

    def test_decay(self) -> None:
        mem = FederatedMemory()
        record = mem.store(MemoryStore.SEMANTIC, "stale belief")
        decayed = mem.decay(record.record_id)
        assert decayed.status == MemoryRecordStatus.DECAYED
        results = mem.retrieve(MemoryStore.SEMANTIC)
        assert len(results) == 0

    def test_evict_remains_queryable(self) -> None:
        mem = FederatedMemory()
        record = mem.store(MemoryStore.SEMANTIC, "evicted item")
        mem.evict(record.record_id)
        assert mem.get(record.record_id).status == MemoryRecordStatus.EVICTED
        results = mem.retrieve(MemoryStore.SEMANTIC)
        assert len(results) == 0

    def test_stale_belief_correction(self) -> None:
        mem = FederatedMemory()
        old = mem.store(MemoryStore.SEMANTIC, "earth is flat", tags=["geography"])
        mem.update_content(old.record_id, "earth is round", "corrected by evidence")
        current = mem.get(old.record_id)
        assert current.content == "earth is round"
        assert current.version == 2


class TestMemoryConsolidator:
    def test_decay_low_salience_records(self) -> None:
        mem = FederatedMemory()
        mem.store(MemoryStore.SEMANTIC, "important", salience=0.8)
        mem.store(MemoryStore.SEMANTIC, "trivial", salience=0.05)
        consolidator = MemoryConsolidator(mem, decay_threshold=0.1)
        result = consolidator.run_consolidation()
        assert result["decayed"] == 1
        active = mem.retrieve(MemoryStore.SEMANTIC)
        assert len(active) == 1

    def test_evict_excess_records(self) -> None:
        mem = FederatedMemory()
        for i in range(10):
            mem.store(MemoryStore.PROCEDURAL, f"strategy_{i}", salience=(i + 1) / 10.0)
        consolidator = MemoryConsolidator(mem, max_per_store=5, decay_threshold=0.0)
        result = consolidator.run_consolidation()
        assert result["evicted"] >= 5

    def test_detect_contradictions(self) -> None:
        mem = FederatedMemory()
        mem.store(MemoryStore.SEMANTIC, "GDP growth is strong", tags=["economy"])
        mem.store(MemoryStore.SEMANTIC, "GDP growth is weak", tags=["economy"])
        consolidator = MemoryConsolidator(mem)
        contradictions = consolidator.detect_contradictions()
        assert len(contradictions) >= 1

    def test_correct_stale_belief(self) -> None:
        mem = FederatedMemory()
        record = mem.store(MemoryStore.SEMANTIC, "old fact")
        consolidator = MemoryConsolidator(mem)
        assert consolidator.correct_stale_belief(record.record_id, "new fact")
        current = mem.get(record.record_id)
        assert current.content == "new fact"

    def test_no_actions_on_clean_memory(self) -> None:
        mem = FederatedMemory()
        mem.store(MemoryStore.SEMANTIC, "good content", salience=0.8)
        consolidator = MemoryConsolidator(mem)
        result = consolidator.run_consolidation()
        assert result["decayed"] == 0
        assert result["evicted"] == 0
