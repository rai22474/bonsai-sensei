# Issues Conocidos

## ~~ISSUE-001~~ — Resuelta: la guía de cultivo ahora es una página wiki markdown

**Síntoma:** Cuando se crea una especie, la guía de cultivo se construye y almacena, pero solo el campo `summary` contiene datos (un blob de texto plano de Tavily). Los campos estructurados — `watering`, `light`, `soil`, `pruning`, `pests` — son siempre `null`. Cuando el usuario pide consejo de cultivo, el LLM tiene que interpretar un blob de texto no estructurado en lugar de consumir campos tipados.

**Causa raíz:** `care_guide_service.py` construye la guía con `watering: None, light: None, ...` hardcodeados — nunca parsea ni extrae datos estructurados de la respuesta de Tavily. El tool de consulta (`get_bonsai_species_by_name`) devuelve el dict `care_guide` tal cual, incluyendo todos los campos nulos.

**Workaround:** Ninguno. El LLM puede extraer información parcial del texto del summary, pero los resultados son inconsistentes.

**Relacionado:** `bonsai_sensei/domain/services/cultivation/species/care_guide_service.py`, `bonsai_sensei/domain/services/cultivation/species/herbarium_tools.py`.

---

## ISSUE-002 — El contexto de conversación se pierde demasiado rápido

**Síntoma:** Tras una conversación corta (unos pocos intercambios con llamadas a tools), el sistema pierde el contexto de lo que se estaba discutiendo. El siguiente mensaje se trata como si la conversación acabara de empezar.

**Causa raíz:** La sesión se resetea cuando `len(session.events) > MAX_SESSION_EVENTS` (actualmente 50). Un único turno de agente con tool calls puede generar 5–10 eventos (mensaje de usuario, respuesta del modelo, tool call, respuesta del tool, respuesta final del modelo). Una conversación de 5–6 pasos puede alcanzar el límite. Al resetear, la sesión se recrea solo con `current_date`, `next_saturday` y `user_location` — no se lleva ningún resumen de conversación hacia adelante.

**Workaround:** Ninguno. Los usuarios deben re-contextualizar tras un reset.

**Relacionado:** `bonsai_sensei/domain/services/advisor.py` (`MAX_SESSION_EVENTS`, `_sync_session`), ADR-004.

---

## ~~ISSUE-003~~ — Resuelta: nombre ambiguo devuelve candidatos y el usuario elige

**Síntoma:** Cuando un usuario pide crear una especie con un nombre genérico (p.ej. "junípero"), el tool resuelve múltiples nombres científicos pero coge el primero silenciosamente (`scientific_names[0]`) y continúa directamente hacia la confirmación. Al usuario nunca se le pregunta qué variedad concreta quiere.

**Causa raíz:** `confirm_create_species_tool.py` toma la primera entrada de `scientific_names` sin comprobar si hay múltiples candidatos. El comportamiento correcto es preguntar al usuario que elija cuando existe más de una coincidencia.

**Workaround:** Los usuarios deben proporcionar el nombre de la variedad exacta desde el principio (p.ej. "Juniperus chinensis" o "junípero chino").

**Relacionado:** `bonsai_sensei/domain/services/cultivation/species/confirm_create_species_tool.py` (línea 49).

---

## ~~ISSUE-005~~ — Resuelta: eliminada dependencia de Google Cloud y Monocle

**Síntoma:** El despliegue requiere credenciales de Google Cloud (`application_default_credentials.json`) montadas como volumen. El `docker-compose.yml` incluye referencias a GCP que bloquean el despliegue en infraestructura sin cuenta Google (nuevo mini PC).

**Causa raíz:** El modelo LLM usa Vertex AI por defecto (`MODEL_PROVIDER=cloud`). La autenticación depende de GCP application default credentials. La telemetría usa Monocle (que escribe ficheros JSON locales) en lugar del stack OpenTelemetry estándar.

**Workaround:** Usar `MODEL_PROVIDER=ollama` con un modelo local, pero Vertex AI sigue siendo la ruta de producción.

**Objetivo:** Eliminar la dependencia de GCP para el despliegue. Usar directamente la Gemini API con API key en lugar de Vertex AI. Eliminar Monocle y usar OpenTelemetry estándar con exportador OTLP hacia Jaeger.

**Relacionado:** `docker-compose.yml`, `bonsai_sensei/observability.py`, `bonsai_sensei/__init__.py`.

---

## ~~ISSUE-006~~ — Resuelta: telemetría migrada a OpenTelemetry estándar con Jaeger

**Síntoma:** Las trazas se vuelcan en ficheros JSON locales en `.monocle/`. Para diagnosticar hay que parsear ficheros manualmente o leer logs de Docker. No hay UI de trazas distribuidas ni capacidad de búsqueda por span/trace.

**Causa raíz:** El stack de observabilidad usa Monocle (`monocle-apptrace`) en lugar del exportador OTLP estándar de OpenTelemetry. No hay Jaeger ni Tempo en el docker-compose.

**Workaround:** Parsear los ficheros `.monocle/*.json` o filtrar `docker logs` con grep.

**Objetivo:** Reemplazar Monocle por el exportador OTLP estándar (`opentelemetry-exporter-otlp`). Añadir Jaeger al `docker-compose.yml` como backend de trazas. Exponer la UI de Jaeger en un puerto local. Opcionalmente, integrar el MCP de Jaeger para que el agente pueda consultar trazas directamente.

**Relacionado:** `bonsai_sensei/observability.py`, `docker-compose.yml`.

---

## ISSUE-008 — Referenciar una especie por nombre científico puede crear una especie duplicada

**Síntoma:** Cuando el usuario pide añadir un bonsái indicando el nombre científico de la especie (en lugar del nombre común), el sistema no encuentra la especie en el catálogo y, en lugar de fallar con un error claro, crea una nueva especie usando el nombre científico como nombre común.

**Causa raíz:** `get_species_by_name_func` busca únicamente por `Species.name` (nombre común). Si el LLM pasa el nombre científico como `common_name`, la búsqueda devuelve `None` y el flujo de creación se activa. No hay búsqueda por `scientific_name` como fallback.

**Workaround:** El usuario debe indicar siempre el nombre común registrado en el catálogo.

**Objetivo:** En las tools que reciben un nombre de especie, hacer búsqueda también por `scientific_name` si la búsqueda por nombre común no devuelve resultados. Alternativamente, usar `search_bonsai_species` (búsqueda parcial) para resolver el nombre antes de operar.

**Relacionado:** `bonsai_sensei/domain/herbarium.py` (`get_species_by_name`), `bonsai_sensei/domain/services/cultivation/species/confirm_create_species_tool.py`, `bonsai_sensei/domain/services/garden/`.

---

## ISSUE-007 — Borrar una especie no comprueba si hay bonsáis que la usan

**Síntoma:** Si el usuario elimina una especie que tiene bonsáis asociados, la operación se ejecuta sin error. Los bonsáis quedan con una referencia a una especie inexistente, corrompiendo el estado de la colección.

**Causa raíz:** `confirm_delete_species_tool.py` llama directamente a `delete_species_func` sin verificar previamente si existe algún bonsái con esa especie. No hay restricción de integridad referencial que lo impida.

**Workaround:** Ninguno. El usuario debe eliminar o reasignar manualmente los bonsáis antes de borrar la especie.

**Objetivo:** En `confirm_delete_species_tool.py`, antes de pedir confirmación, comprobar si hay bonsáis con esa especie usando `list_bonsai_by_species_func`. Si los hay, devolver `{"status": "error", "message": "species_has_bonsai"}` con la lista de nombres afectados.

**Relacionado:** `bonsai_sensei/domain/services/cultivation/species/confirm_delete_species_tool.py`, `bonsai_sensei/domain/garden.py`.

---

## ISSUE-004 — Las respuestas de confirmación acumulan mensajes en el chat

**Síntoma:** Tras aceptar o cancelar una confirmación, el mensaje con botones inline se edita a "Confirmación aceptada." / "Confirmación cancelada." — pero estos mensajes editados permanecen en el chat de forma permanente. En una sesión con varias confirmaciones, el chat se llena de una pila de estos mensajes de estado sin forma de descartarlos.

**Causa raíz:** `handle_confirmation_callback.py` llama a `query.edit_message_text(...)`, que sustituye el botón por un texto estático. No hay mecanismo para colapsar, eliminar o agrupar estos mensajes de estado.

**Workaround:** Ninguno. Los usuarios deben hacer scroll por encima de los mensajes de confirmación acumulados.

**Relacionado:** `bonsai_sensei/telegram/handle_confirmation_callback.py`.
