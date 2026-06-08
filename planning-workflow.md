# Planning Workflow

Multi-step ADK Workflow with HITL for creating cultivation plans (fertilization, phytosanitary, development design).

## Entry point

User asks the **Kikaru** agent to create a plan for a period. Kikaru calls `manage_fertilization_plan`, `manage_phytosanitary_plan`, or `manage_development_plan` — all backed by the same generic `create_manage_plan_tool` in [`manage_plan.py`](bonsai_sensei/src/bonsai_sensei/domain/services/cultivation/plan/manage_plan.py).

## Outer workflow — `manage_plan`

```
START → validate_and_load_context
              ↓ ok
        clarify_objectives  ←──────────────────┐
              ↓ ok                              │ reclarify
        propose_plan ─────────────────────────┘
              ↓ confirm
        create_plan
```

| Node | What it does |
|---|---|
| `validate_and_load_context` | Validates dates; loads bonsai, available products, event history, existing wiki and active plan into workflow state. Short-circuits with error if bonsai not found or no products available. |
| `clarify_objectives` | Delegates to `clarification_runner` (inner workflow). Receives `{ objectives, preferences, context }` or `cancelled`. |
| `propose_plan` | Delegates to `plan_proposal_runner` (inner workflow). Receives confirmed `entries` + `rationale`, or `cancelled`, or `reclarify` → loops back to `clarify_objectives`. |
| `create_plan` | Abandons any active plan (soft-delete future works, marks wiki as abandoned). Creates new plan record + one `PlannedWork` per entry. Writes plan wiki page and updates the plans index wiki page. |

## Inner workflow — clarification loop

[`clarification_runner.py`](bonsai_sensei/src/bonsai_sensei/domain/services/cultivation/plan/clarification_runner.py)

Single node `clarify` with `rerun_on_resume=True`. Uses ADK `RequestInput` interrupt to pause and ask the user.

```
LLM → ClarificationAction
         action = "ask"      → interrupt → ask_human → accumulate in qa_history → restart node
         action = "ask_poll" → interrupt → ask_poll  → accumulate in qa_history → restart node
         action = "done"     → store { objectives, preferences, context } → exit
         action = "cancel"   → { cancelled: True } → exit
```

The LLM sees the full prompt re-rendered with the accumulated Q&A history on each restart. Exits when it has enough info or the user cancels.

**Schema:**
```python
class ClarificationAction(BaseModel):
    action: Literal["ask", "ask_poll", "done", "cancel"]
    question: str
    options: list[str]   # for ask_poll
    objectives: str      # populated on done
    preferences: str
    context: str
```

## Inner workflow — proposal loop

[`plan_proposal_runner.py`](bonsai_sensei/src/bonsai_sensei/domain/services/cultivation/plan/plan_proposal_runner.py)

Single node `propose` with `rerun_on_resume=True`.

```
LLM → ProposalAction
         action = "propose"   → interrupt → ask_plan_review
                                   "confirmed" → store entries → exit
                                   "correct"   → ask_human(feedback) → accumulate in correction_history → restart node
                                   "cancelado" → { cancelled: True } → exit
         action = "reclarify" → { reclarify: True, reason } → exit (outer loops back to clarify_objectives)
         action = "cancel"    → { cancelled: True } → exit
```

### correct vs reclarify

**`correct`** is user-driven. The user reviews the generated plan and asks for adjustments: change dates, modify doses, swap products, reorder entries. The feedback is free text ("move fertilizations to Saturdays", "reduce dose by half"). The planner LLM receives the full `correction_history` and regenerates the plan incorporating it. The user never leaves the proposal loop.

**`reclarify`** is planner-driven. The planner LLM emits it when it determines that the objectives gathered during clarification are insufficient or contradictory to produce a valid plan — for example, the user asked to optimise for growth but no nitrogen-rich fertilizers are available. It signals a fundamental premise failure, not an entry-level adjustment. The outer workflow sends the user back to `clarify_objectives` with a `reclarify_reason` injected into the clarification prompt. The user never triggers this directly.

**Schema:**
```python
class ProposalAction(BaseModel):
    action: Literal["propose", "cancel", "reclarify"]
    display_text: str          # human-readable plan shown to user
    entries: list[dict]        # structured: { date, product_name, dose, notes }
    rationale: str
    correction_prompt: str     # question to ask user on "correct"
```

During review, `outer_tool_context.state["plan_draft_in_progress"]` holds the display text so the outer agent can reference it.

## Session state summary

| Key | Scope | Contents |
|---|---|---|
| `qa_history` | clarification inner session | List of `{ q, a }` pairs |
| `correction_history` | proposal inner session | List of `{ proposal_display, feedback }` |
| `plan_draft_in_progress` | outer ADK tool context | Display text of the current draft (set during review, cleared after) |
| `clarification_result` | clarification inner session | `{ objectives, preferences, context, cancelled }` |
| `proposal_result` | proposal inner session | `{ entries, rationale }` or `{ cancelled }` or `{ reclarify }` |
| `plan_result` | manage_plan outer session | Final `{ status, plan_id, wiki_path, applications }` |

## Key design notes

- All three workflows are independent `InMemoryRunner` instances with ephemeral sessions.
- The `outer_tool_context` is threaded into sub-runners so they can write to the outer agent's session state.
- All LLM prompts are Jinja2 templates under each plan type's `templates/` directory.
- `manage_plan` is generic; fertilization, phytosanitary, and design each bind it via a thin factory that supplies type-specific parameters (`plan_class`, `work_type`, `product_*_key`, `wiki_path_prefix`).
- On plan replacement: future planned works are deleted, the existing plan's wiki page gets an `## Abandonment` section appended, status flipped to `abandoned`.
