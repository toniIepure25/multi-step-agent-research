# ASAR Scientific Discovery — Stage 1 Runtime Certification

**Date:** 2026-08-14  
**Starting SHA:** c8ef5c8fab08dedf9f94a442ea2613c1621b751f  
**Branch:** feature/asar-ree-v2

---

## Environment

| Field | Value |
|-------|-------|
| Python | 3.12.13 |
| Environment | `.venv` (project virtualenv) |
| Dependency source | `pip install -e ".[dev]"` from pyproject.toml |
| Proxy/certificate issue | Bypassed — used existing `python3.12` binary at `~/.local/bin/` |
| Workaround | Created .venv with existing Python 3.12 instead of `uv` toolchain download |
| Key dependencies | pydantic 2.13.4, pytest 9.1.1 |

---

## Test Results

| Suite | Result |
|-------|--------|
| Scientific Discovery tests | **111 passed** |
| Full repository suite | **557 passed, 1 skipped** |

---

## State Certification

| Criterion | Status |
|-----------|--------|
| Deterministic replay | **PASS** |
| Immutability | **PASS** |
| Fork independence | **PASS** |
| Serialization round-trip | **PASS** |
| Event provenance | **PASS** |
| No hidden mutation | **PASS** |

---

## Belief Metamorphic Invariants

| Invariant | Status |
|-----------|--------|
| Decisive refutation never increases belief | **PASS** |
| Strong support increases belief | **PASS** |
| Irrelevant evidence ≈ zero update | **PASS** |
| Duplicate evidence not double-counted | **PASS** |
| Dependent evidence reduced effect | **PASS** |
| Evidence reversal flips direction | **PASS** |
| Order robustness (divergence < 0.1) | **PASS** |
| Extreme confidence bounded [0,1] | **PASS** |
| Non-identifiability: no artificial separation | **PASS** |

---

## Controlled Worlds

| World | Recovery (B3) | Refut. Sens. (B3) | Stickiness (B3) |
|-------|---------------|-------------------|-----------------|
| Confirmation trap | 1.000 | 0.387 | 0.000 |
| Confounded causality | 1.000 | 0.400 | 0.000 |
| Non-identifiable | 0.000 (correct) | 0.000 | 0.000 |
| Reverse causality | 1.000 | 0.400 | 0.000 |
| Null world | 1.000 | 0.400 | 0.074 |
| Measurement artifact | 1.000 | 0.400 | 0.000 |

---

## Policies

| ID | Name | Implemented | Recovery |
|----|------|-------------|----------|
| B0 | Passive Update | ✓ | 0.833 |
| B1 | Confirmation Seeker | ✓ | 0.667 |
| B2 | Random Challenge | ✓ | 0.833 |
| B3 | Falsification-First | ✓ | 0.833 |
| B4 | Oracle | ✓ | 1.000 |

---

## SD-H1: Falsification Advantage

**N = 60** (6 world types × 10 seeds, DEV split)

| Metric | B3 | B0 | Δ | 95% CI | p |
|--------|-----|-----|---|--------|---|
| Recovery Accuracy | 0.833 | 0.833 | 0.000 | [0, 0] | — |
| Refutation Sensitivity | 0.397 | 0.372 | **+0.021** | [+0.015, +0.026] | **< 0.0001** |
| Theory Stickiness | 0.012 | 0.028 | **-0.016** | [-0.023, -0.010] | **< 0.0001** |
| False Abandonment | 0.000 | 0.000 | 0.000 | — | — |

---

## Behavioral Influence

| Criterion | Status |
|-----------|--------|
| ON/OFF produce different events | **PASS** |
| Belief trajectories differ | **PASS** |
| Theory stickiness lower with ON | **PASS** |
| No oracle leakage | **PASS** |
| Content influence (targeted > passive) | **PASS** |
| Proposals have positive EIG | **PASS** |
| Proposals target leading hypothesis | **PASS** |
| Non-identifiable: correct abstention | **PASS** |
| Null world: correct rejection | **PASS** |

---

## GO/NO-GO

| Criterion | Status |
|-----------|--------|
| STATE_REPLAY | **PASS** |
| IMMUTABILITY | **PASS** |
| BELIEF_METAMORPHIC_TESTS | **PASS** |
| BEHAVIORAL_INFLUENCE | **PASS** (p < 0.0001) |
| NO_ORACLE_LEAKAGE | **PASS** |
| FALSIFICATION_CONTENT_INFLUENCE | **PASS** |
| SD-H1 RECOVERY | **PASS** (not worse) |
| SD-H1 SENSITIVITY | **PASS** (Δ=+0.021, exceeds SESOI) |
| FALSE_ABANDONMENT | **PASS** (rate=0.000) |
| NULL_WORLD | **PASS** |

---

## STAGE 1 VERDICT: **GO**

All 10/10 criteria met. Falsification-first control demonstrably changes scientific behavior in the correct direction with no increase in false abandonment.
