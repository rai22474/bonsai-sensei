from prometheus_client import Counter, Histogram

LLM_REQUEST_DURATION = Histogram(
    "llm_request_duration_seconds",
    "LLM call duration in seconds",
    ["model"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0],
)

LLM_REQUESTS_TOTAL = Counter(
    "llm_requests_total",
    "Total number of LLM calls",
    ["model", "status"],
)

LLM_TOKENS_TOTAL = Counter(
    "llm_tokens_total",
    "Total LLM tokens consumed",
    ["model", "token_type"],
)


WIKI_REQUEST_DURATION = Histogram(
    "wiki_request_duration_seconds",
    "Wiki HTTP call duration in seconds",
    ["operation"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)

WIKI_REQUESTS_TOTAL = Counter(
    "wiki_requests_total",
    "Total number of wiki HTTP calls",
    ["operation", "status"],
)
