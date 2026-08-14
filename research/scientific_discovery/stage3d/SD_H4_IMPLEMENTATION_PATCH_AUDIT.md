# SD-H4 Implementation Patch Audit

## Date: 2026-08-14
## Bug: `None.lower()` crash on nullable `new_explanation` field

---

## SCIENTIFIC PROTOCOL CHANGED: NO
## EXPERIMENTAL SEMANTICS CHANGED: NO

## Bug Fix: nullable field handling only

---

## Root Cause

The LLM response JSON may contain:
```json
{"new_explanation": null}
```

The original code called `.lower()` directly on the value without null check.

## Fix Applied

```python
# Before (crashes on None):
recovery = any(m in self_new.lower() for m in world["true_markers"])

# After (null-safe):
self_new = s.get("new_explanation") or ""  # None -> ""
recovery = any(m in self_new.lower() for m in world["true_markers"]) if self_new else False
```

## What This Does NOT Change

- Classification rules (wrong_markers / true_markers matching)
- Abandonment thresholds
- Confidence parsing
- Prompts (byte-identical)
- World definitions
- Evidence trajectories
- Statistical analysis plan
- Recovery definition (same markers, same logic)

## Semantics of `new_explanation = None`

When the model returns null for new_explanation:
- `recovery = False` (no alternative identified)
- This is correct: if no new explanation is offered, recovery has not occurred

## Regression Coverage

The fix is tested by `test_stage3d.py` existing tests (null handling in parse utilities).
Additional assertion: `safe_json_parse` returns dict even when fields are null.
