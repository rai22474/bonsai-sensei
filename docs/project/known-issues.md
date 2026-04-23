# Issues Conocidos

## ISSUE-002 — El contexto de conversación se pierde demasiado rápido

**Síntoma:** Tras una conversación corta (unos pocos intercambios con llamadas a tools), el sistema pierde el contexto de lo que se estaba discutiendo. El siguiente mensaje se trata como si la conversación acabara de empezar.

**Causa raíz:** La sesión se resetea cuando `len(session.events) > MAX_SESSION_EVENTS` (actualmente 50). Un único turno de agente con tool calls puede generar 5–10 eventos (mensaje de usuario, respuesta del modelo, tool call, respuesta del tool, respuesta final del modelo). Una conversación de 5–6 pasos puede alcanzar el límite. Al resetear, la sesión se recrea solo con `current_date`, `next_saturday` y `user_location` — no se lleva ningún resumen de conversación hacia adelante.

**Workaround:** Ninguno. Los usuarios deben re-contextualizar tras un reset.

**Relacionado:** `bonsai_sensei/domain/services/advisor.py` (`MAX_SESSION_EVENTS`, `_sync_session`), ADR-004.

---

## ~~ISSUE-004~~ — Las respuestas de confirmación acumulan mensajes en el chat ✅ Resuelto

**Solución:** Al aceptar, el mensaje de confirmación se edita a "⏳ Procesando..." para dar feedback inmediato. Al cancelar, se edita a "Cancelando...". En ambos casos se registra `pending["on_resume"] = query.message.delete` para que `ask_confirmation` elimine el mensaje en cuanto el agente retoma la ejecución. El resultado es que el mensaje desaparece solo cuando el tool se reanuda, sin acumulación permanente en el chat.

**Relacionado:** `bonsai_sensei/telegram/handle_confirmation_callback.py`, `bonsai_sensei/domain/services/human_input.py`.

---

## ISSUE-007 — Borrar una especie no comprueba si hay bonsáis que la usan

**Síntoma:** Si el usuario elimina una especie que tiene bonsáis asociados, la operación se ejecuta sin error. Los bonsáis quedan con una referencia a una especie inexistente, corrompiendo el estado de la colección.

**Causa raíz:** `confirm_delete_species_tool.py` llama directamente a `delete_species_func` sin verificar previamente si existe algún bonsái con esa especie. No hay restricción de integridad referencial que lo impida.

**Workaround:** Ninguno. El usuario debe eliminar o reasignar manualmente los bonsáis antes de borrar la especie.

**Objetivo:** En `confirm_delete_species_tool.py`, antes de pedir confirmación, comprobar si hay bonsáis con esa especie usando `list_bonsai_by_species_func`. Si los hay, devolver `{"status": "error", "message": "species_has_bonsai"}` con la lista de nombres afectados.

**Relacionado:** `bonsai_sensei/domain/services/cultivation/species/confirm_delete_species_tool.py`, `bonsai_sensei/domain/garden.py`.

---

## ISSUE-008 — Referenciar una especie por nombre científico puede crear una especie duplicada

**Síntoma:** Cuando el usuario pide añadir un bonsái indicando el nombre científico de la especie (en lugar del nombre común), el sistema no encuentra la especie en el catálogo y, en lugar de fallar con un error claro, crea una nueva especie usando el nombre científico como nombre común.

**Causa raíz:** `get_species_by_name_func` busca únicamente por `Species.name` (nombre común). Si el LLM pasa el nombre científico como `common_name`, la búsqueda devuelve `None` y el flujo de creación se activa. No hay búsqueda por `scientific_name` como fallback.

**Workaround:** El usuario debe indicar siempre el nombre común registrado en el catálogo.

**Objetivo:** En las tools que reciben un nombre de especie, hacer búsqueda también por `scientific_name` si la búsqueda por nombre común no devuelve resultados. Alternativamente, usar `search_bonsai_species` (búsqueda parcial) para resolver el nombre antes de operar.

**Relacionado:** `bonsai_sensei/domain/herbarium.py` (`get_species_by_name`), `bonsai_sensei/domain/services/cultivation/species/confirm_create_species_tool.py`, `bonsai_sensei/domain/services/garden/`.
