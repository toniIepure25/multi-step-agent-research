"""
Stage 3B — Generative Scientist.

Connects a real LLM to the validated scientific kernel.
All generative outputs pass through typed schema parsing.
No unparsed prose becomes authoritative ScientificState.

The LLM provides:
  - Creative hypothesis generation
  - Mechanistic alternatives
  - Prediction derivation
  - Falsifier generation
  - Experiment proposals

The kernel provides:
  - Belief accounting
  - Experiment scoring
  - Evidence evaluation
  - Recovery measurement
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from pydantic import BaseModel, Field, ValidationError

from asar.core.llm import (
    LLMClientProtocol,
    LLMGenerationRequest,
    LLMGenerationResponse,
    LLMMessage,
    MessageRole,
)
from asar.scientific_discovery.capability_gate import (
    CapabilityLevel,
    CapabilityResult,
    GeneratedAlternative,
    GeneratedExperiment,
    GeneratedFalsifier,
    GeneratedHypothesis,
    GeneratedPrediction,
    ModelCapabilityReport,
)


# ---------------------------------------------------------------------------
# Model Manifest
# ---------------------------------------------------------------------------


class ModelManifest(BaseModel):
    """Frozen record of which model is being used and its configuration."""

    model_id: str
    model_version: str = ""
    temperature: float = 0.7
    max_tokens: int = 2048
    provider: str = "openai"
    frozen_date: str = ""


# ---------------------------------------------------------------------------
# Scientific Prompt Templates
# ---------------------------------------------------------------------------


HYPOTHESIS_PROMPT = """You are a rigorous scientific researcher. Given the following observations and problem context, generate a structured scientific hypothesis.

PROBLEM:
{problem}

OBSERVATIONS:
{observations}

Generate a hypothesis in EXACTLY this JSON format:
{{
  "claim": "<what you claim is happening>",
  "mechanism": "<the causal mechanism you propose>",
  "scope": "<what domain/conditions this applies to>",
  "assumptions": ["<assumption 1>", "<assumption 2>"],
  "predictions": ["<testable prediction 1>", "<testable prediction 2>"],
  "falsifiers": ["<observation that would disprove this>"]
}}

Respond with ONLY the JSON object, no other text."""


ALTERNATIVES_PROMPT = """You are a scientific critic. Given the following hypothesis, generate a MECHANISTICALLY DISTINCT alternative explanation. Do NOT paraphrase the original — propose a genuinely different causal mechanism.

PRIMARY HYPOTHESIS:
Claim: {claim}
Mechanism: {mechanism}

OBSERVATIONS:
{observations}

Generate an alternative in EXACTLY this JSON format:
{{
  "claim": "<different claim>",
  "mechanism": "<genuinely different causal mechanism>",
  "how_it_differs": "<why this is mechanistically distinct>",
  "predictions_different_from_primary": ["<prediction where this alternative differs>"]
}}

Respond with ONLY the JSON object, no other text."""


PREDICTION_PROMPT = """Given the following hypothesis and proposed experiment, derive what outcome you predict.

HYPOTHESIS:
Claim: {claim}
Mechanism: {mechanism}

EXPERIMENT:
{experiment}

Generate a prediction in EXACTLY this JSON format:
{{
  "experiment": "{experiment_id}",
  "predicted_outcome": "<what you predict will be observed>",
  "confidence": <0.0 to 1.0>,
  "reasoning": "<why this mechanism predicts this outcome>"
}}

Respond with ONLY the JSON object, no other text."""


FALSIFIER_PROMPT = """You are a scientific falsifier. Given the following hypothesis, propose an observation that, if made, would substantially reduce confidence in this hypothesis.

HYPOTHESIS:
Claim: {claim}
Mechanism: {mechanism}
Predictions: {predictions}

Generate a falsifier in EXACTLY this JSON format:
{{
  "observation_that_would_falsify": "<specific observation>",
  "why_this_falsifies": "<why this observation contradicts the mechanism>",
  "how_to_test": "<how to look for this observation>"
}}

Respond with ONLY the JSON object, no other text."""


EXPERIMENT_PROMPT = """You are designing a discriminating scientific experiment. Given two competing hypotheses, propose an experiment whose outcome would differ depending on which hypothesis is correct.

HYPOTHESIS A:
Claim: {claim_a}
Mechanism: {mechanism_a}

HYPOTHESIS B:
Claim: {claim_b}
Mechanism: {mechanism_b}

Generate an experiment proposal in EXACTLY this JSON format:
{{
  "experiment_description": "<what to do>",
  "what_it_tests": "<what distinction it tests>",
  "predicted_outcome_if_h1": "<what H1 predicts>",
  "predicted_outcome_if_h2": "<what H2 predicts>",
  "why_discriminating": "<why these predictions differ>"
}}

Respond with ONLY the JSON object, no other text."""


# ---------------------------------------------------------------------------
# Core Generative Scientist
# ---------------------------------------------------------------------------


class GenerativeScientist:
    """
    Connects an LLM to the scientific kernel through typed schema parsing.

    Every LLM output is parsed into a typed schema before entering
    the scientific state. Failed parses are logged and counted.
    """

    def __init__(
        self,
        client: LLMClientProtocol,
        manifest: ModelManifest,
    ) -> None:
        self._client = client
        self._manifest = manifest
        self._parse_failures: list[dict[str, Any]] = []
        self._total_calls: int = 0
        self._successful_parses: int = 0

    @property
    def schema_compliance_rate(self) -> float:
        if self._total_calls == 0:
            return 0.0
        return self._successful_parses / self._total_calls

    @property
    def parse_failures(self) -> list[dict[str, Any]]:
        return list(self._parse_failures)

    async def generate_hypothesis(
        self,
        problem: str,
        observations: list[str],
    ) -> Optional[GeneratedHypothesis]:
        """C1: Generate a structured hypothesis from observations."""
        prompt = HYPOTHESIS_PROMPT.format(
            problem=problem,
            observations="\n".join(f"- {o}" for o in observations),
        )
        return await self._generate_and_parse(prompt, GeneratedHypothesis, "C1_hypothesis")

    async def generate_alternative(
        self,
        claim: str,
        mechanism: str,
        observations: list[str],
    ) -> Optional[GeneratedAlternative]:
        """C2: Generate a mechanistically distinct alternative."""
        prompt = ALTERNATIVES_PROMPT.format(
            claim=claim,
            mechanism=mechanism,
            observations="\n".join(f"- {o}" for o in observations),
        )
        return await self._generate_and_parse(prompt, GeneratedAlternative, "C2_alternative")

    async def generate_prediction(
        self,
        claim: str,
        mechanism: str,
        experiment: str,
        experiment_id: str = "exp",
    ) -> Optional[GeneratedPrediction]:
        """C3: Derive prediction for hypothesis under experiment."""
        prompt = PREDICTION_PROMPT.format(
            claim=claim,
            mechanism=mechanism,
            experiment=experiment,
            experiment_id=experiment_id,
        )
        return await self._generate_and_parse(prompt, GeneratedPrediction, "C3_prediction")

    async def generate_falsifier(
        self,
        claim: str,
        mechanism: str,
        predictions: list[str],
    ) -> Optional[GeneratedFalsifier]:
        """C4: Propose a falsifying observation."""
        prompt = FALSIFIER_PROMPT.format(
            claim=claim,
            mechanism=mechanism,
            predictions="\n".join(f"- {p}" for p in predictions),
        )
        return await self._generate_and_parse(prompt, GeneratedFalsifier, "C4_falsifier")

    async def generate_experiment(
        self,
        claim_a: str,
        mechanism_a: str,
        claim_b: str,
        mechanism_b: str,
    ) -> Optional[GeneratedExperiment]:
        """C6: Propose a discriminating experiment."""
        prompt = EXPERIMENT_PROMPT.format(
            claim_a=claim_a,
            mechanism_a=mechanism_a,
            claim_b=claim_b,
            mechanism_b=mechanism_b,
        )
        return await self._generate_and_parse(prompt, GeneratedExperiment, "C6_experiment")

    async def _generate_and_parse(
        self,
        prompt: str,
        schema: type[BaseModel],
        capability_id: str,
    ) -> Optional[BaseModel]:
        """Generate LLM response and parse into typed schema."""
        self._total_calls += 1

        request = LLMGenerationRequest(
            model=self._manifest.model_id,
            messages=[
                LLMMessage(role=MessageRole.USER, content=prompt),
            ],
            temperature=self._manifest.temperature,
            max_tokens=self._manifest.max_tokens,
        )

        try:
            response = await self._client.generate(request)
        except Exception as e:
            self._parse_failures.append({
                "capability": capability_id,
                "error_type": "provider_failure",
                "error": str(e),
            })
            return None

        # Parse response into schema
        result = _parse_json_response(response.output_text, schema)
        if result is not None:
            self._successful_parses += 1
            return result

        # Attempt repair: strip markdown fences
        cleaned = _strip_markdown_fences(response.output_text)
        result = _parse_json_response(cleaned, schema)
        if result is not None:
            self._successful_parses += 1
            return result

        self._parse_failures.append({
            "capability": capability_id,
            "error_type": "parse_failure",
            "raw_output": response.output_text[:500],
        })
        return None


# ---------------------------------------------------------------------------
# Self-Authorship Experiment Runner
# ---------------------------------------------------------------------------


class SelfAuthorshipRunner:
    """
    Runs the SD-H4 self-authorship experiment.

    Generates a hypothesis, then tests whether the system treats it differently
    when marked as self-generated vs externally-provided.
    """

    def __init__(self, scientist: GenerativeScientist) -> None:
        self._scientist = scientist

    async def generate_hypothesis_for_world(
        self,
        problem: str,
        observations: list[str],
    ) -> Optional[GeneratedHypothesis]:
        """Generate a hypothesis that will be used in both conditions."""
        return await self._scientist.generate_hypothesis(problem, observations)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_json_response(text: str, schema: type[BaseModel]) -> Optional[BaseModel]:
    """Attempt to parse text as JSON into a Pydantic schema."""
    try:
        data = json.loads(text)
        return schema.model_validate(data)
    except (json.JSONDecodeError, ValidationError):
        return None


def _strip_markdown_fences(text: str) -> str:
    """Remove markdown code fences from LLM output."""
    lines = text.strip().split("\n")
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()
