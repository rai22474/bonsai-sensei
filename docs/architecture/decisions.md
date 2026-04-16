# Architecture Decisions

## ADR-001 — Staying on ADK; LangGraph migration discarded

**Status:** Decided

**Context:**
The system was originally built with Google ADK. A migration to LangGraph was considered to use its `interrupt` mechanism, which allows pausing graph execution mid-node and resuming exactly where it stopped after receiving user input. This would enable true human-in-the-loop within a plan execution — something ADK cannot do natively (see ISSUE-001).

**Decision:**
Remain on ADK. LangGraph's `interrupt` solves the mid-execution dialogue problem, but it imposes a strict graph model where all agent interactions must be explicitly wired as nodes and edges. This rigidity prevents rich conversational flows: agents lose the ability to have free, multi-turn exchanges driven by context. The cost is too high for a system whose core value is conversational decision support (see ADR-005).

ISSUE-001 is accepted as a known architectural constraint. Plans must be designed as atomic, independent operations that do not require mid-execution user input.

**Consequences:**
- The ADK `InMemoryRunner` and `BuiltInPlanner` remain the execution backbone.
- Multi-turn conversations work naturally via ADK session state.
- Confirmations are handled via a session-state injection workaround (ADR-006), which only supports binary accept/cancel decisions.
- Plans with dependent steps that require user input between steps are not supported.

---

## ADR-002 — sensei → command_pipeline (mitori + shokunin) as SequentialAgent

**Status:** Accepted

**Context:**
Queries and commands require different handling. Queries are direct (tools answer immediately). Commands require planning (what steps?) and execution (run each step with the right agent).

**Decision:**
- `sensei` (root Agent): routes between direct query tools and `command_pipeline` via AgentTool. Presents results to the user. Never delegates presentation to another agent.
- `command_pipeline` (SequentialAgent): composed of `mitori → shokunin`.
  - `mitori` (LlmAgent with BuiltInPlanner): analyzes the request and generates an `action_plan` JSON with ordered steps and agent assignments. Output stored in `output_key="action_plan"`.
  - `shokunin` (LlmAgent): reads `action_plan` from state and executes each step by calling the appropriate specialist AgentTools.

**Consequences:**
- sensei has a single responsibility: route and present.
- mitori has a single responsibility: plan.
- shokunin has a single responsibility: execute.
- Format and tone instructions live only in sensei's prompt.

---

## ADR-003 — Plan cleanup belongs to the executor, not the planner

**Status:** Accepted

**Context:**
`mitori` writes `action_plan` via `output_key`. `shokunin` reads and executes it. The question is who resets plan state after execution.

**Decision:**
State cleanup (`action_plan`, `current_step`) belongs to the executor that knows when the plan has finished. Shokunin resets plan state once all steps are completed. The same principle applies to `kikaku`/`seko`: seko should own `cultivation_plan` and `cultivation_step` cleanup, not kikaku.

**Consequences:**
- Presenters and planners have no state-management responsibility.
- Known outstanding debt: kikaku still resets `cultivation_plan` in its `after_agent` hook (see DEBT-001).

---

## ADR-004 — Free-form agents for conversational nodes

**Status:** Accepted

**Context:**
Nodes like `fertilizer_advisor` and `phytosanitary_advisor` are conversational by nature. Applying the same rigid pipeline pattern (mitori+shokunin, explicit planning) to them adds overhead without benefit.

**Decision:**
Conversational and advisory agents use `create_agent` with `system_prompt` only — no multi-step planning pipeline, no explicit routing, no state fields. They have tools for reading data and respond freely. This keeps them simple and readable.

**Consequences:**
- These nodes are easy to add and reason about.
- Multi-turn conversation within a single graph execution works naturally.
- They are not candidates for the mitori/shokunin pipeline unless they require confirmations or multi-agent coordination.

---

## ADR-005 — System vision: conversational decision support

**Status:** Accepted

**Context:**
The system's core value is helping users make decisions in the complex domain of bonsai cultivation. Structured operations (creating plans, registering treatments) are secondary — they exist to maintain a knowledge base that enriches conversations.

**Decision:**
Architectural decisions should favor conversational flexibility over pipeline control. Strict planning pipelines (mitori/shokunin) are reserved for command operations that need agent coordination. Everything else should be as free-form as possible.

**Consequences:**
- Two major use cases not yet implemented: diagnostic conversation flow and standard plan generation per species/design. Both should follow the free-form agent pattern (ADR-004), not the mitori/shokunin pipeline.
- Adding `active_mode` state or complex routing for conversational flows should be avoided unless strictly necessary.

---

## ADR-006 — Confirmation pattern: async injection via session state

**Status:** Accepted

**Context:**
ADK does not support mid-execution interrupts. Commands that modify data (create, update, delete, apply) require explicit user approval before executing. The solution must work within ADK's execution model.

**Decision:**
1. **Registration**: confirmation tools register a `Confirmation` in `ConfirmationStore` (with an `execute` callback) and return a `"confirmation_pending"` marker instead of executing immediately.
2. **Detection**: shokunin detects `confirmation_pending` in a step result, records it, and continues to the next step without re-calling the tool.
3. **Presentation**: after `advise()` completes, pending confirmations are returned in `AdvisorResponse.pending_confirmations` and presented to the user as inline action buttons.
4. **Resolution**: when the user accepts or cancels, `apply_confirmation_decision` runs the `Confirmation.execute()` callback (or skips it) and calls `inject_confirmation_result`, which appends a summary string to `session.state["pending_confirmation_results"]`. When all confirmations are resolved, `summarize_session=True` is also set.
5. **Context propagation**: at the start of the next `advise()` call, `_sync_session` pops `pending_confirmation_results` from state. `_build_user_message` prepends them as a system context block so the LLM knows which actions were already executed.

**Consequences:**
- Per-step confirmations are possible without LangGraph interrupts.
- The LLM always has confirmation outcomes as explicit context on the next turn.
- The user experience is asynchronous: the agent responds immediately, confirmations arrive as follow-up buttons.
- This pattern only supports binary decisions (accept/cancel). Mid-plan dialogue and dependent-step plans are not supported (see ISSUE-001).

---

## ADR-007 — Session management: reset with summary on overflow or completion

**Status:** Accepted

**Context:**
ADK's `InMemoryRunner` accumulates events in session. Long sessions degrade performance and may hit token limits. After all confirmations are resolved, the session's work is complete and old state is noise.

**Decision:**
Sessions are reset (deleted and recreated) when either:
- `session.state["summarize_session"] == True` (set when all pending confirmations are resolved), or
- `len(session.events) > MAX_SESSION_EVENTS` (currently 50).

On reset, a summary of the confirmed actions is extracted from `pending_confirmation_results` and carried forward as a `session_summary` string. This summary is prepended to the next user message as `[Resumen de sesión anterior: ...]` so the LLM retains continuity.

**Consequences:**
- Session memory is bounded; no unbounded growth.
- Conversational continuity is preserved across resets via the summary.
- The summary only captures confirmed actions, not the full conversation history.
