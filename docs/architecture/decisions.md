# Architecture Decisions

## ADR-001 — Migration from ADK to LangGraph

**Status:** In progress

**Context:**
The system was originally built with Google ADK. ADK handles multi-turn conversations naturally and gives agents autonomy to decide when to ask for more information. However, ADK's confirmation model is limited: shokunin batches all confirmations and presents them to the user at the end of execution. There is no way to interrupt mid-execution to get per-step user approval.

**Decision:**
Migrate to LangGraph to use its `interrupt` mechanism, which allows pausing graph execution at any point to wait for user confirmation before resuming.

**Consequences:**
- Per-step confirmations are now possible and explicit.
- Multi-turn conversational flows become harder: every user message re-enters the graph at START → sensei, requiring sensei to re-infer conversation context each turn. In ADK, agents could sustain multi-turn conversations natively.
- The migration should be conservative: use LangGraph's strict graph control only where confirmations are needed. Conversational agents (advisors, diagnosis) should remain as free-form as possible.

---

## ADR-002 — Sensei as router, tsutae as presenter

**Status:** Accepted

**Context:**
In ADK, sensei was both router and presenter — it responded directly to the user after receiving pipeline results. In LangGraph this created a node with two responsibilities and two exit points.

**Decision:**
Split into two nodes:
- `sensei`: pure router. Never responds to the user directly. Routes to `query_pipeline` (after using query tools) or `command_pipeline` (for write operations). Has two routing tools: `query_pipeline` and `command_pipeline`.
- `tsutae`: single presenter. The only node that speaks to the user. Receives results from both query flows and command pipeline flows.

**Consequences:**
- Each node has a single, clear responsibility.
- The format/tone instructions live only in tsutae.
- Sensei's prompt contains only routing logic.

---

## ADR-003 — Plan cleanup belongs to the orchestrator, not the planner

**Status:** Accepted

**Context:**
Initially `after_agent` hooks in sensei and tsutae reset `action_plan` and `current_step`. This meant the planner node knew about plan lifecycle management.

**Decision:**
State cleanup (`action_plan=None`, `current_step=0`) belongs to shokunin, which is the node that knows when a plan has finished executing. Shokunin resets plan state in all its `Command(goto="tsutae")` calls.

**Consequences:**
- tsutae has no middleware and no state responsibility — it only presents.
- The same principle should be applied to kikaku/seko: seko should own `cultivation_plan` and `cultivation_step` cleanup, not kikaku.

---

## ADR-004 — Free-form agents for conversational nodes

**Status:** Accepted

**Context:**
Nodes like `fertilizer_advisor` and `phytosanitary_advisor` are conversational by nature. Applying the same rigid pipeline pattern (middleware, state management, explicit routing) to them adds overhead without benefit.

**Decision:**
Conversational/advisory agents use `create_agent` with `system_prompt` only — no middleware, no state fields, no explicit routing. They have tools for reading data and respond freely. This matches the ADK model for these nodes.

**Consequences:**
- These nodes are simple, readable, and easy to add.
- Multi-turn conversation within a single graph execution works naturally.
- Multi-turn across user message turns still has the sensei re-routing problem (see ADR-001).

---

## ADR-005 — System vision: conversational decision support

**Status:** Accepted

**Context:**
The system's core value is helping users make decisions in the complex domain of bonsai cultivation. Structured operations (creating plans, registering treatments) are secondary — they exist to maintain a knowledge base that enriches conversations.

**Decision:**
Architectural decisions should favor conversational flexibility over pipeline control. LangGraph's strict graph control is reserved for confirmation flows. Everything else should be as free-form as possible.

**Consequences:**
- Two major use cases not yet implemented: diagnostic conversation flow and standard plan generation per species/design. Both should follow the free-form agent pattern, not the mitori/shokunin pipeline.
- Adding `active_mode` state or complex routing for conversational flows should be avoided unless strictly necessary.
