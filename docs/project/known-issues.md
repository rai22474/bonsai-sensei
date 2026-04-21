# Issues Conocidos

## ISSUE-001 — La guía de cultivo se crea pero los campos estructurados nunca se rellenan

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

## ISSUE-003 — Un nombre común ambiguo de especie lanza la creación sin pedir precisión

**Síntoma:** Cuando un usuario pide crear una especie con un nombre genérico (p.ej. "junípero"), el tool resuelve múltiples nombres científicos pero coge el primero silenciosamente (`scientific_names[0]`) y continúa directamente hacia la confirmación. Al usuario nunca se le pregunta qué variedad concreta quiere.

**Causa raíz:** `confirm_create_species_tool.py` toma la primera entrada de `scientific_names` sin comprobar si hay múltiples candidatos. El comportamiento correcto es preguntar al usuario que elija cuando existe más de una coincidencia.

**Workaround:** Los usuarios deben proporcionar el nombre de la variedad exacta desde el principio (p.ej. "Juniperus chinensis" o "junípero chino").

**Relacionado:** `bonsai_sensei/domain/services/cultivation/species/confirm_create_species_tool.py` (línea 49).

---

## ISSUE-004 — Las respuestas de confirmación acumulan mensajes en el chat

**Síntoma:** Tras aceptar o cancelar una confirmación, el mensaje con botones inline se edita a "Confirmación aceptada." / "Confirmación cancelada." — pero estos mensajes editados permanecen en el chat de forma permanente. En una sesión con varias confirmaciones, el chat se llena de una pila de estos mensajes de estado sin forma de descartarlos.

**Causa raíz:** `handle_confirmation_callback.py` llama a `query.edit_message_text(...)`, que sustituye el botón por un texto estático. No hay mecanismo para colapsar, eliminar o agrupar estos mensajes de estado.

**Workaround:** Ninguno. Los usuarios deben hacer scroll por encima de los mensajes de confirmación acumulados.

**Relacionado:** `bonsai_sensei/telegram/handle_confirmation_callback.py`.
