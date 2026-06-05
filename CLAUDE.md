# AGENT INSTRUCTION RULES:
All agent instructions follow this fixed schema:

```
<Opening line> — one sentence: who the agent is and their domain. No # Rol header.

# Contexto          (only if dynamic variables are present: dates, plan, available agents)
<template variables or injected content>

# <Domain section>  (only when two or more distinct operational modes exist, e.g. reads vs. writes)
<content>

# Comportamiento    (always present if there are non-obvious rules)
<bullet points: sequencing, fallback, output format constraints>
Do NOT describe what tools do internally — that belongs in tool docstrings.

# Formato           (only for agents that talk directly to the user)
<language and formatting rules>
```

Sections that would contain only one trivial line are omitted.

Forbidden:
- `#ROL`, `# OBJETIVO`, `# INSTRUCCIONES` headers — the opening line replaces them.
- Instructions that duplicate tool docstrings (e.g. "validates that the bonsai exists internally").
- The phrase "Usa las herramientas disponibles para cada operación" as the only behavioral guidance.
- Naming specific tool function names in agent instructions. Describe the intent or behavior; the model reads tool docstrings to decide which tool to call.

# LANGUAGE RULES: 
- Ensure all comments and logs are in English.

# DOCUMENTATION RULES: 
- Do not add docstrings to functions/methods if the name is self-explanatory. - Only add docstrings if they explain "why" something is done or complex behavior that isn't obvious from the signature.
- Always add docstrings for tool functions so ADK can use them for tool descriptions, even if the name is self-explanatory.
- Do not use comments inside functions/methods. Instead, ensure function and variable names are self-explanatory. STRICTLY FORBIDDEN to generate comments explaining code logic.

# ERROR HANDLING: 
- Never catch generic Exceptions just for logging purposes. Let them bubble up to the global exception handler.

# IMPORT RULES: 
- Never use relative imports (e.g., `from .module import func`). Always use absolute imports (e.g., `from package.module import func`).
DESIGN RULES:
- Inject external dependencies into functions for testability (e.g., translators, HTTP clients, API clients). Never instantiate API clients (e.g., `genai.Client`) or read `os.getenv` inside a function body — use a factory function that accepts the dependency and returns a closure.
- Never use single-letter or abbreviated variable names (e.g., `c`, `e`, `f`). Always use descriptive names, including in list comprehensions and lambda expressions.
- Never hardcode user-facing strings (questions, confirmation texts, error messages) inside domain tools. Any text that reaches the user must be defined in `telegram/messages/` and injected as a `Callable` (e.g. `build_selection_question`, `build_confirmation_message`). Tools call the callable — they never build the string.
- When an operation requires first fetching an ID and then acting on it (list → pick → execute), merge both steps into a single tool that accepts the entity name, resolves the ID internally, and handles selection via `ask_selection` if multiple results exist. Never expose the ID-lookup step as a separate tool the LLM must orchestrate.
- Service operations (execute_*, run_*) must receive ALL I/O dependencies as `Callable` parameters — including reads, writes, and side effects. No direct calls to I/O functions (filesystem, network, DB) inside these functions. Factory functions (create_*) act as composition roots: they resolve raw config (paths, URLs, models) into callables and bind them via `functools.partial`. This two-layer pattern makes service functions pure and unit-testable with mocks only, no filesystem or network needed. See `execute_create_fertilizer` / `create_create_fertilizer_tool` and `run_wiki_dreamer` / `create_wiki_dreamer` as canonical examples.

# DOMAIN RULES: 
- Keep domain entities in `bonsai_sensei/domain`, not in `bonsai_sensei/database`.
- LLM prompt contexts (strings passed to LLM runners) must always be built with a Jinja2 template, never with string concatenation or f-strings. Place templates in the `templates/` subdirectory next to the runner file.

# TESTING RULES:
- Use a single assert per test.
- Use `assert_that` from pyhamcrest: `assert_that(actual, matcher, "reason")`. Prefer `equal_to`, `not_none`, `has_key`, `not_`, `contains_string`. The reason string is optional when the matcher description is self-explanatory.
- Prefer pytest fixtures for test data setup.
- Name tests with a should_ prefix.
- Place fixtures below tests in test files.
- Always include failure messages in assert statements (the reason parameter in `assert_that`).
- Only test public method, private methods are implementation details.
- Follow TDD: always write the acceptance test first, then implement the production code to make it pass.
- In acceptance tests, the `cleanup_records` fixture MUST delete ALL resources created during the test — including files on disk (photos, wiki pages, etc.). Always add a REST endpoint to delete them and call it in cleanup before deleting the parent entity.
- Acceptance test steps have strict boundaries on how they interact with the system:
  - `given` steps: MUST use REST API only. NEVER call `advise()` or `accept_confirmation()`. These are preconditions that must be deterministic and fast. The LLM may normalize or paraphrase input (e.g., "10 g" → "10g"), breaking assertions. If the required REST endpoint does not exist, create it.
  - `when` steps: MUST use `advise()` (and `accept_confirmation()` if needed). These are the user actions under test.
  - `then` steps: MUST use REST API only. NEVER call `advise()`. Assertions must be based on deterministic data from the API, not on LLM-generated text unless that text is the explicit subject of the test.
- Each acceptance test scenario MUST use an isolated ADK session. The `context` fixture in every test module's `conftest.py` MUST include `"user_id": f"bdd-<suite>-{uuid.uuid4().hex}"`. Never hardcode a fixed user_id string — shared sessions cause `tool_call_counters` to accumulate across scenarios, producing false failures. The global `reset_adk_session_after_test` fixture in `acceptance-tests/conftest.py` resets the session only when `context["user_id"]` is set.

