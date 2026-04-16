# Known Issues

## ISSUE-001 — Conversational agents are single-turn within the pipeline

**Symptom:** When a user wants to have a back-and-forth conversation with an advisor (e.g., fertilizer_advisor) during plan creation, only one exchange is possible. The advisor returns its response to seko and seko moves to the next step.

**Root cause:** Seko executes each plan step once and moves on. It has no mechanism to pause for user feedback between steps (unlike the interrupt-based confirmation flow).

**Workaround:** None currently. Users must provide all context upfront in their request.

**Related:** DEBT-002, ADR-001.

---

## ISSUE-002 — sensei may misroute continuation messages in conversational flows

**Symptom:** Not yet observed (conversational flows not implemented), but expected: if a user is in a multi-turn diagnostic conversation and sends a follow-up like "could it be fungal?", sensei may interpret it as a new query rather than a continuation.

**Root cause:** Every message re-enters at sensei with no explicit conversation mode state.

**Workaround:** Not applicable yet.

**Related:** DEBT-002.
