from prometheus_client import Counter, Histogram

EPISODE_DURATION_SECONDS = Histogram(
    "em_episode_duration_seconds",
    "Duration of add_episode() call including Graphiti LLM extraction",
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0, 120.0],
)

EPISODES_TOTAL = Counter(
    "em_episodes_total",
    "Total number of episodes submitted",
    ["status"],
)

SEARCH_REQUESTS_TOTAL = Counter(
    "em_search_requests_total",
    "Total number of memory search requests",
    ["status"],
)

OBSERVATIONS_RETURNED_TOTAL = Counter(
    "em_observations_returned_total",
    "Total number of observations returned to the dreamer",
)
