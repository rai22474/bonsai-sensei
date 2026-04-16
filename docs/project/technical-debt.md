# Technical Debt

## DEBT-001 — kikaku owns cultivation plan cleanup (should be seko)

**Module:** `bonsai_sensei/domain/services/cultivation/plan/kikaku.py`

**Description:**
`KikakuMiddleware.after_agent` writes `cultivation_plan` and `cultivation_step` to state. By the principle established in ADR-003, this cleanup should belong to seko (the executor that knows when the plan is done), not to kikaku (the planner).

**Impact:** Low. Works correctly but violates the responsibility principle.

**Fix:** Move plan state reset to seko's `Command(goto=...)` calls, same pattern applied to shokunin.

---

## DEBT-002 — Multi-turn conversational routing through sensei

**Module:** `bonsai_sensei/domain/services/sensei.py`

**Description:**
Every user message re-enters the graph at START → sensei. For multi-turn conversational flows (diagnosis, design discussion), sensei must infer from message history which conversational agent to route back to. This is fragile and adds overhead not present in the ADK version.

**Impact:** Medium. No current user-facing feature depends on multi-turn agent conversations yet, but both planned use cases (diagnostic flow, standard plan generation) will hit this problem.

**Fix:** Design pending. Options discussed: state-based `active_mode` field vs trusting message history. Decision deferred until conversational use cases are implemented.

---

## DEBT-003 — Diagnostic and standard plan use cases not implemented

**Module:** `bonsai_sensei/domain/services/`

**Description:**
Two core use cases identified but not yet implemented:
1. Diagnostic conversation: symptom → disease expert → advisor collaboration → optional plan
2. Standard plan generation: per bonsai species and design style, recalculated on demand

**Impact:** High on product value. These are central to the system's purpose as a decision support tool.

**Fix:** Implement as free-form agents following the `fertilizer_advisor` pattern (ADR-004). A disease expert node is needed for use case 1.
