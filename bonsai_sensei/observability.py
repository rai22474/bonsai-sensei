import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)

_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "bonsai-sensei")
_ENVIRONMENT = os.getenv("DEPLOYMENT_ENV", "production")
_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317")


def _build_resource() -> Resource:
    return Resource.create({
        SERVICE_NAME: _SERVICE_NAME,
        "service.version": os.getenv("SERVICE_VERSION", "unknown"),
        "deployment.environment": _ENVIRONMENT,
    })


def _setup_tracing(resource: Resource) -> None:
    exporter = OTLPSpanExporter(endpoint=_OTLP_ENDPOINT, insecure=True)
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(exporter))
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
    logger.info("OpenTelemetry initialized: service=%s env=%s endpoint=%s", _SERVICE_NAME, _ENVIRONMENT, _OTLP_ENDPOINT)
