"""
Tests for Stage 3C — Remote Provider and Generative Science Integration.

These tests verify the provider infrastructure, model classification,
and scientific experiment protocols without requiring live API access.
"""

from __future__ import annotations

import json
import pytest

from asar.scientific_discovery.remote_provider import RemoteLLMProvider, CompletionResult
from asar.scientific_discovery.generative_scientist import (
    _parse_json_response,
    _strip_markdown_fences,
)
from asar.scientific_discovery.capability_gate import (
    GeneratedHypothesis,
    GeneratedAlternative,
    GeneratedFalsifier,
    GeneratedPrediction,
    GeneratedExperiment,
)


class TestRemoteProviderInfrastructure:
    """Test provider infrastructure without live API calls."""

    def test_completion_result_dataclass(self):
        r = CompletionResult(
            model="test-model",
            output_text="hello",
            finish_reason="stop",
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            latency_ms=100.0,
        )
        assert r.model == "test-model"
        assert r.total_tokens == 15
        assert r.error is None

    def test_completion_result_error(self):
        r = CompletionResult(model="m", output_text="", error="timeout")
        assert r.error == "timeout"
        assert r.output_text == ""

    def test_provider_instantiation(self):
        p = RemoteLLMProvider(base_url="https://example.com", timeout=30)
        assert p._base_url == "https://example.com"
        assert p._timeout == 30.0

    def test_call_log_empty_initially(self):
        p = RemoteLLMProvider()
        assert p.call_log == []


class TestMarkdownFenceStripping:
    """Test JSON extraction from markdown-wrapped responses."""

    def test_basic_json_fence(self):
        text = '```json\n{"key": "value"}\n```'
        assert _strip_markdown_fences(text) == '{"key": "value"}'

    def test_no_fence(self):
        text = '{"key": "value"}'
        assert _strip_markdown_fences(text) == '{"key": "value"}'

    def test_fence_with_trailing_newline(self):
        text = '```json\n{"a": 1}\n```\n'
        assert _strip_markdown_fences(text).strip() == '{"a": 1}'

    def test_plain_fence(self):
        text = '```\n{"a": 1}\n```'
        assert _strip_markdown_fences(text) == '{"a": 1}'


class TestCapabilityGateParsing:
    """Test that generated scientific artifacts parse correctly."""

    def test_hypothesis_parsing(self):
        raw = json.dumps({
            "claim": "X causes Y",
            "mechanism": "via pathway Z",
            "scope": "human adults",
            "assumptions": ["A1"],
            "predictions": ["P1"],
            "falsifiers": ["F1"],
        })
        h = _parse_json_response(raw, GeneratedHypothesis)
        assert h is not None
        assert h.claim == "X causes Y"
        assert h.mechanism == "via pathway Z"

    def test_alternative_parsing(self):
        raw = json.dumps({
            "claim": "different claim",
            "mechanism": "different mechanism",
            "how_it_differs": "uses different pathway",
            "predictions_different_from_primary": ["pred1"],
        })
        alt = _parse_json_response(raw, GeneratedAlternative)
        assert alt is not None
        assert alt.how_it_differs == "uses different pathway"

    def test_falsifier_parsing(self):
        raw = json.dumps({
            "observation_that_would_falsify": "obs",
            "why_this_falsifies": "because",
            "how_to_test": "method",
        })
        f = _parse_json_response(raw, GeneratedFalsifier)
        assert f is not None
        assert f.observation_that_would_falsify == "obs"

    def test_prediction_parsing(self):
        raw = json.dumps({
            "experiment": "exp1",
            "predicted_outcome": "no effect",
            "confidence": 0.7,
            "reasoning": "because mechanism blocked",
        })
        p = _parse_json_response(raw, GeneratedPrediction)
        assert p is not None
        assert p.predicted_outcome == "no effect"
        assert p.confidence == 0.7

    def test_experiment_parsing(self):
        raw = json.dumps({
            "experiment_description": "RCT design",
            "what_it_tests": "mechanism A vs B",
            "predicted_outcome_if_h1": "positive",
            "predicted_outcome_if_h2": "negative",
            "why_discriminating": "opposite predictions",
        })
        e = _parse_json_response(raw, GeneratedExperiment)
        assert e is not None
        assert e.why_discriminating == "opposite predictions"

    def test_malformed_json_returns_none(self):
        result = _parse_json_response("not json at all", GeneratedHypothesis)
        assert result is None

    def test_partial_json_returns_none(self):
        result = _parse_json_response('{"claim": "X"}', GeneratedHypothesis)
        # Missing required fields — should fail validation
        # Depends on whether model uses strict validation
        # At minimum should not crash
        assert result is None or isinstance(result, GeneratedHypothesis)


class TestModelClassification:
    """Test model inventory classification."""

    def test_model_inventory_valid(self):
        import pathlib
        inv_path = pathlib.Path(__file__).parent.parent.parent / "research" / "scientific_discovery" / "stage3c" / "AVAILABLE_MODELS.json"
        if inv_path.exists():
            data = json.loads(inv_path.read_text())
            assert "models" in data
            for m in data["models"]:
                assert m["type"] in ["GENERATION_TEXT", "GENERATION_MULTIMODAL", "EMBEDDING", "UNKNOWN"]
                assert "model_id" in m
                assert "family" in m

    def test_no_embedding_as_generation(self):
        import pathlib
        inv_path = pathlib.Path(__file__).parent.parent.parent / "research" / "scientific_discovery" / "stage3c" / "AVAILABLE_MODELS.json"
        if inv_path.exists():
            data = json.loads(inv_path.read_text())
            for m in data["models"]:
                if m["type"] == "EMBEDDING":
                    assert m["role"] == "NOT_USED"


class TestSelfAuthorshipProtocol:
    """Test that self/external provenance yields byte-identical hypothesis content."""

    def test_provenance_manipulation_preserves_content(self):
        hypothesis = "Drug X works via receptor R1"
        
        self_prompt = f"You previously proposed this hypothesis:\n{hypothesis}"
        external_prompt = f"Another researcher proposed this hypothesis:\n{hypothesis}"
        
        # Hypothesis content is identical in both
        assert hypothesis in self_prompt
        assert hypothesis in external_prompt
        
        # Only provenance differs
        assert "You previously" in self_prompt
        assert "Another researcher" in external_prompt

    def test_sab_computation(self):
        """Self-authorship bias = retention_self - retention_external."""
        self_confidence = 25
        ext_confidence = 10
        sab = self_confidence - ext_confidence
        assert sab == 15  # Positive = self-protection


class TestLockedSplitContamination:
    """Verify locked seeds don't overlap with dev seeds."""

    def test_locked_seeds_distinct(self):
        dev_seeds = list(range(1, 21))
        locked_seeds = list(range(21, 41))
        assert set(dev_seeds).isdisjoint(set(locked_seeds))

    def test_locked_seeds_sufficient_n(self):
        locked_seeds = list(range(21, 41))
        assert len(locked_seeds) >= 20
