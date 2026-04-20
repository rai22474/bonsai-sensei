# Technical Debt

## DEBT-002 — OpenTelemetry exports to console in local/acceptance environments

**Area:** `bonsai_sensei/observability.py`, `docker-compose.yml`

**Problem:** When `GOOGLE_CLOUD_PROJECT` is not set, all spans and metrics are exported to stdout via `ConsoleSpanExporter` and `ConsoleMetricExporter`. This floods application logs with large JSON telemetry payloads, making them hard to read. The acceptance test Docker logs are particularly affected.

**Trade-off:** The console output is currently useful for automated diagnosis — grep on Docker logs lets Claude (and developers) inspect exact tool call args and responses during acceptance test failures (e.g. catching LLM passing IDs instead of names). Removing it without a replacement would lose that observability.

**Desired state:** Route traces to Jaeger (or another OTLP-compatible backend) in local and acceptance environments. Keep console output available selectively for debugging. Requires deciding whether diagnosis via log grep is worth preserving or whether Jaeger UI covers the need.

**Effort:** Low — add `opentelemetry-exporter-otlp-proto-http` dependency, add OTLP branch in `_setup_tracing`/`_setup_metrics`, add Jaeger service to `docker-compose.yml` and `docker-compose.acceptance.yml`.
