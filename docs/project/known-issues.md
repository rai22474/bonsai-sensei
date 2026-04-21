# Known Issues

## ISSUE-001 — Care guide is created but structured fields are never populated

**Symptom:** When a species is created, the care guide is built and stored, but only the `summary` field contains data (a raw text blob from Tavily). The structured fields — `watering`, `light`, `soil`, `pruning`, `pests` — are always `null`. When a user asks for cultivation advice, the LLM has to interpret an unstructured text blob instead of consuming typed fields.

**Root cause:** `care_guide_service.py` builds the guide with `watering: None, light: None, ...` hardcoded — it never parses or extracts structured data from the Tavily response. The consultation tool (`get_bonsai_species_by_name`) returns the raw `care_guide` dict as-is, including all null fields.

**Workaround:** None. The LLM may extract partial information from the summary text, but results are inconsistent.

**Related:** `bonsai_sensei/domain/services/cultivation/species/care_guide_service.py`, `bonsai_sensei/domain/services/cultivation/species/herbarium_tools.py`.

---

## ISSUE-002 — Conversation context is lost too quickly

**Symptom:** After a short conversation (a few exchanges involving tool calls), the system loses context of what was being discussed. The next message is handled as if the conversation just started.

**Root cause:** The session resets whenever `len(session.events) > MAX_SESSION_EVENTS` (currently 50). A single agent turn with tool calls can generate 5–10 events (user message, model response, tool call, tool response, final model response). A 5–6 step conversation can hit the limit. On reset, the session is recreated with only `current_date`, `next_saturday`, and `user_location` — no conversation summary is carried forward. The old summary-on-reset mechanism (from ADR-007) was removed when the confirmation flow was refactored.

**Workaround:** None. Users must re-state context after a reset.

**Related:** `bonsai_sensei/domain/services/advisor.py` (`MAX_SESSION_EVENTS`, `_sync_session`), ADR-007.

---

## ISSUE-003 — Ambiguous common species name triggers creation without disambiguation

**Symptom:** When a user asks to create a species with a generic name (e.g., "juniper"), the tool resolves multiple scientific names but silently picks the first one (`scientific_names[0]`) and proceeds directly to confirmation. The user is never asked which specific variety they want.

**Root cause:** `confirm_create_species_tool.py` takes the first entry from `scientific_names` without checking if there are multiple candidates. The right behavior is to ask the user to choose when more than one match exists.

**Workaround:** Users must provide the exact variety name upfront (e.g., "Juniperus chinensis" or "chinese juniper").

**Related:** `bonsai_sensei/domain/services/cultivation/species/confirm_create_species_tool.py` (line 49).

---

## ISSUE-004 — Confirmation responses leave a clutter of messages in the chat

**Symptom:** After accepting or cancelling a confirmation, the inline button message is edited to "Confirmación aceptada." / "Confirmación cancelada." — but these edited messages stay in the chat permanently. In a session with several confirmations, the chat fills with a stack of these status messages with no way to dismiss them.

**Root cause:** `handle_confirmation_callback.py` calls `query.edit_message_text(...)` which replaces the button with a static text message. There is no mechanism to collapse, delete, or group these follow-up status messages.

**Workaround:** None. Users must scroll past the accumulated confirmation status messages.

**Related:** `bonsai_sensei/telegram/handle_confirmation_callback.py`.
