import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor, SpanExporter, SpanExportResult

from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)

_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "bonsai-sensei")
_ENVIRONMENT = os.getenv("DEPLOYMENT_ENV", "production")
_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317")


class _FileSpanExporter(SpanExporter):
    """Writes spans as JSONL to a file for post-run diagnostics."""

    def __init__(self, filepath: str) -> None:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self._filepath = filepath

    def export(self, spans):
        with open(self._filepath, "a") as file:
            for span in spans:
                file.write(span.to_json() + "\n")
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        pass


def _build_resource() -> Resource:
    return Resource.create({
        SERVICE_NAME: _SERVICE_NAME,
        "service.version": os.getenv("SERVICE_VERSION", "unknown"),
        "deployment.environment": _ENVIRONMENT,
    })


def _setup_tracing(resource: Resource) -> None:
    traces_file = os.getenv("OTEL_TRACES_FILE")
    if traces_file:
        exporter = _FileSpanExporter(traces_file)
        processor = SimpleSpanProcessor(exporter)
    else:
        exporter = OTLPSpanExporter(endpoint=_OTLP_ENDPOINT, insecure=True)
        processor = BatchSpanProcessor(exporter)
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)


def init_telemetry() -> None:
    if os.getenv("OBSERVABILITY_ENABLED", "true").lower() != "true":
        return
    resource = _build_resource()
    try:
        _setup_tracing(resource)
    except Exception as exc:
        logger.warning("Failed to initialize telemetry exporters: %s", exc)
    LoggingInstrumentor().instrument(set_logging_format=True)
    HTTPXClientInstrumentor().instrument()
    traces_file = os.getenv("OTEL_TRACES_FILE")
    destination = traces_file if traces_file else _OTLP_ENDPOINT
    logger.info("OpenTelemetry initialized: service=%s env=%s destination=%s", _SERVICE_NAME, _ENVIRONMENT, destination)
