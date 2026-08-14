# Falsification Boost Anti-Tautology Audit

**Date:** 2026-08-14  
**Auditor:** Automated  
**Status:** CRITICAL METHODOLOGICAL REVIEW

---

## 1. What `_compute_falsification_boost()` Does

The function receives:
- `state: ScientificState` — current belief state (observable to any policy)
- `evidence: ScientificEvidence` — incoming evidence item (observable to any policy)
- `active_proposal: Optional[FalsificationProposal]` — output of FalsificationEngine

It returns `None` (no boost) unless ALL conditions hold:
1. `active_proposal` exists (falsification was proposed this round)
2. `evidence.direction_for(target_hid) == CONTRADICTING` (evidence contradicts the proposal target)
3. `relevance >= 0.3` (evidence is at least minimally relevant to target)

When triggered, it returns:
- `{target_hid: 1.5}` (amplified update for target)
- `{alt_hid: 1.2}` (amplified update for alternatives that receive SUPPORTING direction)
- `{other: 1.0}` (no boost for others)

---

## 2. What Inputs It Sees

| Input | Source | Privileged? | Available to B0? |
|-------|--------|-------------|------------------|
| `active_proposal.target_hypothesis_id` | FalsificationEngine output | NO — derived from `state.ecology.top_hypothesis()` | B0 could compute same |
| `evidence.direction_for(target_hid)` | Evidence item field | NO — same evidence object passed to all policies | YES |
| `evidence.relevance_to_hypotheses` | Evidence item field | NO — same for all | YES |
| `evidence.direction_for(alt_hid)` | Evidence item field | NO — same for all | YES |

---

## 3. Does It See Evaluator Truth?

| Question | Answer |
|----------|--------|
| Does it access `WorldGroundTruth`? | **NO** |
| Does it access `correct_hypothesis_id`? | **NO** |
| Does it access `world_type`? | **NO** |
| Does it access `decisive_round`? | **NO** |
| Does it access future evidence? | **NO** |

**VERDICT: No oracle leakage.**

---

## 4. Is the Advantage Tautological?

### The Core Question:

> Could a skeptical reviewer reasonably say that B3 wins because the benchmark grants evidence matching its own falsifier a special update bonus?

### Analysis:

**YES — there IS a methodological concern.** The boost is not tautological in the sense of using oracle information, but it IS mechanically tied to a property of the evidence that is **equally observable** by B0.

The boost fires when:
1. Evidence contradicts the leading hypothesis
2. Evidence relevance to that hypothesis ≥ 0.3

These are properties **already encoded in the evidence item's metadata fields** (`direction_per_hypothesis`, `relevance_to_hypotheses`). B0 processes this same evidence through the same `BeliefUpdater` but without the 1.5× amplification.

**The B3 advantage therefore comes from:**
- Recognizing that contradicting evidence for the leading hypothesis is "more important" (1.5× independence)
- This is a **handcrafted update rule**, not a learned or derived scientific judgment

### Is This Scientifically Legitimate?

**Partially.** The argument for the boost:
> "A scientist who has identified what would falsify their theory, and then observes that falsification, should respond MORE strongly than one who encounters the same evidence passively."

This is a reasonable **attention/recognition** argument. But the current implementation:
1. Uses ONLY hypothesis rank and evidence metadata to trigger
2. Does NOT check semantic correspondence between the proposed falsifier's content and the evidence content
3. Does NOT verify that the falsification proposal was *specifically* about this type of evidence
4. The proposal targets the `top_hypothesis()` — which is simply the highest-belief hypothesis

### Severity:

**MODERATE.** The mechanism is:
- Not oracle-leaking
- Not semantically matching (just structural matching on direction + relevance)
- But it grants B3 an unconditional amplification that B0 lacks, triggered by the same observable signals

---

## 5. What Would a Redesign Look Like?

A more defensible version would:
1. Check whether the evidence content semantically matches the specific falsifier's `statement`
2. OR: Remove the boost entirely and test whether the POLICY of seeking falsifiers (not amplifying updates) provides value → This is the **B3-ZERO** test

---

## 6. Required Remediation

| Action | Status |
|--------|--------|
| Implement B3-ZERO (falsification policy, no boost) | REQUIRED |
| Compare B3-ZERO vs B0 to isolate policy vs boost | REQUIRED |
| Test shuffled falsifier (cross-world) to verify semantic dependency | REQUIRED |
| Document interpretation clearly in results | REQUIRED |
| Consider reducing boost to 1.0 (effectively B3-ZERO) if policy alone provides value | RECOMMENDED |

---

## 7. Verdict

**The boost audit identifies a real methodological concern but NOT a fatal flaw:**

- The boost does not use oracle/privileged information
- The boost fires on evidence properties equally visible to B0
- But B3 receives an unconditional amplification that B0 lacks
- The amplification is parameterized (1.5) without principled derivation
- B3-ZERO is ESSENTIAL to interpret whether the falsification POLICY has independent value

**Classification: PASS WITH REQUIRED CONTROLS**

The locked evaluation must include B3-ZERO. The primary SD-H1 interpretation must decompose:
1. Effect of falsification policy (B3-ZERO - B0)
2. Effect of recognition boost (B3 - B3-ZERO)
