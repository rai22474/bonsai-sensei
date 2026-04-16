# Known Issues

## ISSUE-001 — No existe human-in-the-loop dentro de un plan en ejecución

**Symptom:** Once a plan is executing (mitori → shokunin), there is no mechanism to pause, interact with the user, and resume. This manifests in several ways:
- A plan with dependent steps (create species → create bonsai → generate cultivation plan) breaks silently: shokunin continues past a `confirmation_pending` step, so dependent steps run against state that doesn't exist yet.
- After a confirmation is resolved, the original plan is gone. The next user message re-enters at sensei, which reconstructs a partial plan from a session summary — relying on LLM inference rather than a deterministic continuation.
- Mid-plan dialogue is impossible: if an agent tool needs to ask the user a question (not just accept/cancel), it cannot. All user communication goes through sensei, which only activates between full execution cycles.

**Root cause:** ADK's `InMemoryRunner` runs agents to completion. Sub-agents (AgentTools) have no way to pause execution, surface a message to the user, and resume from the same point. The confirmation pattern (ADR-006) is a workaround for the binary accept/cancel case only — it is not a general human-in-the-loop mechanism.

**Workaround:** Plans must be designed so that each confirmation is an independent, atomic operation with no dependent steps following it. Multi-step plans with dependencies that require user input between steps are not supported.

**Related:** ADR-006, ADR-001.
