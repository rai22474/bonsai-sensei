from prometheus_client import Counter, Gauge, Histogram

LLM_REQUEST_DURATION = Histogram(
    "kb_llm_request_duration_seconds",
    "LLM call duration in seconds",
    ["model"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0],
)

LLM_REQUESTS_TOTAL = Counter(
    "kb_llm_requests_total",
    "Total number of LLM calls",
    ["model", "status"],
)

LLM_TOKENS_TOTAL = Counter(
    "kb_llm_tokens_total",
    "Total LLM tokens consumed",
    ["model", "token_type"],
)

DREAMER_RUNS_TOTAL = Counter(
    "kb_dreamer_runs_total",
    "Total number of dreamer runs",
    ["outcome"],
)

DREAMER_PAGES_CHANGED_TOTAL = Counter(
    "kb_dreamer_pages_changed_total",
    "Total wiki pages changed by the dreamer",
)

WIKI_REVIEW_ACTIONS_TOTAL = Counter(
    "kb_wiki_review_actions_total",
    "Total wiki page review decisions by the admin",
    ["action"],
)
