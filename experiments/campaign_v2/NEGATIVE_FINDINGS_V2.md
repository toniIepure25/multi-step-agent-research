# Campaign V2 — Negative Findings

## 1. B1 Fixed Strategy Outperforms Full Adaptive REE

**Finding**: B1_reflection (quality=0.562) beats full_ree (quality=0.378) on dev set,
confirmed on locked test (0.594 vs 0.356). B1 wins 4 of 5 families.

**Why it matters**: The entire premise of adaptive metacognitive scheduling is that
selecting the right cognitive operation improves quality. If a fixed 5-step strategy
beats the adaptive scheduler, the scheduling mechanism is worse than useless.

**Root cause**: Attack operator crowding. The heuristic market's falsification_value
bonus (0.4) causes attack_hypothesis to dominate selection (46% of all operations).
Most attack operations return NO_OP because they repeatedly target the same hypothesis.

## 2. The Epistemic Market Is Anti-Calibrated at System Level

**Finding**: Round-robin selection produces higher quality than the heuristic market
on 2 of 5 families (ignorance_discovery: 0.79 vs 0.34; false_majority: 0.42 vs 0.19).

**Why it matters**: If random operator cycling beats the bid-based scheduler, the
market weights contain negative information about operator value.

## 3. DiversityAwareMarket Does Not Help

**Finding**: Adding a consecutive-selection penalty to the market produces 0.333 quality
vs 0.352 for heuristic. The penalty is not strong enough and addresses symptoms, not cause.

## 4. Self-Model, Stopping Policy, and Market Ablation Are Non-Causal

**Finding**: Disabling self_model, stopping_policy, or epistemic_market via ablation
flags produces identical behavior to full_ree. Quality, operator sequences, and
tokens used are all identical.

**Root cause**: The controller defaults mask the interventions. When self_model=False,
a neutral prior (1.0) is used, but since no custom self_model is provided in the
standard campaign, the default (0.7) is used in both cases. Stopping thresholds are
never met. Market ablation passes None, which defaults to EpistemicMarket().

## 5. REE Quality Does Not Improve With Budget

**Finding**: At budgets 2k, 5k, 10k, 20k tokens, full_ree quality is constant at 0.378.
The controller stops at ~5500 tokens regardless of available budget.

**Why it matters**: If more compute doesn't help, the system is either solving everything
it can or wasting compute on unproductive operations (the latter, given attack crowding).

## 6. Oracle Action Values Are Nearly Uncorrelated With Realized Quality

**Finding**: Oracle-realized correlation r = 0.031.

**Why it matters**: The oracle computes the true information value of each action
from the latent world. The fact that this doesn't predict realized quality means
continuation policy (what happens AFTER the forced action) dominates outcomes.
Single-action value prediction is insufficient for scheduling.

## 7. Feature Importance Correlations Are Weak

**Finding**: Maximum |r| between state features and rule accuracy is 0.162 (evidence_count).
Hypothesis entropy, ignorance priority, and contradiction density have near-zero correlation.

**Why it matters**: If state features don't predict which action is best, the rich
epistemic state representation may not justify its overhead for scheduling purposes.

## 8. Campaign V1 Mocks Were Content-Independent

**Preserved finding from V1**: Mock operators produced outputs that didn't depend on
problem content, making all architectures achieve identical 33% substring match.
This invalidated all Campaign V1 quality comparisons.

## 9. Hypothesis Ecology Is Necessary But Not Sufficient

**Finding**: Removing hypothesis_ecology drops quality 90% (d ≈ 1.4), but having it
ON doesn't match B1. The hypothesis generation mechanism works, but the market
doesn't allocate enough operations to it (only 12% of selections).

## 10. "Always Retrieve" Is the Best Simple Policy

**Finding**: The majority baseline (always select retrieve, 51.6% accuracy) outperforms
the simple state-based rule (34.8%). This is because most forked states are early
in episodes where evidence collection is objectively most valuable.
