import os

from opentelemetry import metrics, trace
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)

_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "bonsai-sensei")
_ENVIRONMENT = os.getenv("DEPLOYMENT_ENV", "production")
_METRICS_EXPORT_INTERVAL_MS = 60_000


def _build_resource() -> Resource:
    return Resource.create({
        SERVICE_NAME: _SERVICE_NAME,
        "service.version": os.getenv("SERVICE_VERSION", "unknown"),
        "deployment.environment": _ENVIRONMENT,
    })


def _setup_tracing(resource: Resource) -> None:
    if os.getenv("GOOGLE_CLOUD_PROJECT"):
        from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
        exporter = CloudTraceSpanExporter()
    else:
        exporter = ConsoleSpanExporter()
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


def _setup_metrics(resource: Resource) -> None:
    if os.getenv("GOOGLE_CLOUD_PROJECT"):
        from opentelemetry.exporter.cloud_monitoring import CloudMonitoringMetricsExporter
        exporter = CloudMonitoringMetricsExporter()
    else:
        exporter = ConsoleMetricExporter()
    reader = PeriodicExportingMetricReader(exporter, export_interval_millis=_METRICS_EXPORT_INTERVAL_MS)
    provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(provider)


def init_telemetry() -> None:
    if os.getenv("OBSERVABILITY_ENABLED", "true").lower() != "true":
        return
    resource = _build_resource()
    try:
        _setup_tracing(resource)
        _setup_metrics(resource)
    except Exception as exc:
        logger.warning("Failed to initialize telemetry exporters: %s", exc)
    LoggingInstrumentor().instrument(set_logging_format=True)
    HTTPXClientInstrumentor().instrument()
    logger.info("OpenTelemetry initialized: service=%s env=%s", _SERVICE_NAME, _ENVIRONMENT)
