# Deuda Técnica

## DEBT-002 — OpenTelemetry exporta a consola en entornos local y de aceptación

**Área:** `bonsai_sensei/observability.py`, `docker-compose.yml`

**Problema:** Cuando `GOOGLE_CLOUD_PROJECT` no está configurado, todos los spans y métricas se exportan a stdout via `ConsoleSpanExporter` y `ConsoleMetricExporter`. Esto inunda los logs de la aplicación con grandes payloads JSON de telemetría, haciéndolos difíciles de leer. Los logs de Docker en los tests de aceptación se ven especialmente afectados.

**Trade-off:** La salida por consola es actualmente útil para diagnóstico automatizado — hacer grep sobre los logs de Docker permite a Claude (y a los desarrolladores) inspeccionar los args y respuestas exactos de las llamadas a tools durante fallos en los tests de aceptación (p.ej. detectar cuando el LLM pasa IDs en vez de nombres). Eliminarlo sin un reemplazo supondría perder esa observabilidad.

**Estado deseado:** Enrutar los traces a Jaeger (u otro backend compatible con OTLP) en entornos local y de aceptación. Mantener la salida por consola disponible selectivamente para depuración. Requiere decidir si el diagnóstico via grep de logs vale la pena preservarlo o si la UI de Jaeger cubre la necesidad.

**Esfuerzo:** Bajo — añadir dependencia `opentelemetry-exporter-otlp-proto-http`, añadir rama OTLP en `_setup_tracing`/`_setup_metrics`, añadir servicio Jaeger a `docker-compose.yml` y `docker-compose.acceptance.yml`.
