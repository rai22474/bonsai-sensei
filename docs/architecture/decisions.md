# Decisiones de Arquitectura

## ADR-001 — Continuar con ADK; migración a LangGraph descartada

**Estado:** Decidido

**Contexto:**
El sistema se construyó originalmente con Google ADK. Se consideró migrar a LangGraph para usar su mecanismo `interrupt`, que permite pausar la ejecución de un grafo en mitad de un nodo y reanudarla exactamente donde se detuvo tras recibir input del usuario. Esto habría habilitado un human-in-the-loop real dentro de la ejecución de un plan, algo que ADK no soporta de forma nativa.

**Decisión:**
Continuar con ADK. El `interrupt` de LangGraph resuelve el problema del diálogo mid-ejecución, pero impone un modelo de grafo estricto donde todas las interacciones entre agentes deben estar cableadas explícitamente como nodos y aristas. Esta rigidez impide flujos conversacionales ricos: los agentes pierden la capacidad de mantener intercambios libres y multi-turno guiados por contexto. El coste es demasiado alto para un sistema cuyo valor central es el soporte conversacional a la toma de decisiones (ver `docs/project/vision.md`).

El problema del human-in-the-loop se resolvió sin LangGraph mediante suspensión async de tools: los tools son funciones `async` que hacen `await ask_confirmation()` / `await ask_human()`, suspendiendo la ejecución vía `asyncio.Event` hasta que el usuario responde. El event loop del runner de ADK queda libre para procesar los mensajes entrantes de Telegram que desbloquean el tool suspendido.

**Consecuencias:**
- El `InMemoryRunner` y el `BuiltInPlanner` de ADK siguen siendo el motor de ejecución.
- Las conversaciones multi-turno funcionan de forma natural via estado de sesión de ADK.
- Los tools con interacción de usuario usan `ask_confirmation` / `ask_human` (ADR-003) — bloqueo async real, no un workaround de session state.
- Los planes con pasos dependientes que requieren confirmación del usuario entre pasos están soportados.

---

## ADR-002 — sensei → command_pipeline (mitori + shokunin) como SequentialAgent

**Estado:** Aceptado

**Contexto:**
Las consultas y los comandos requieren tratamiento diferente. Las consultas son directas (los tools responden inmediatamente). Los comandos requieren planificación (¿qué pasos?) y ejecución (ejecutar cada paso con el agente adecuado).

**Decisión:**
- `sensei` (Agent raíz): enruta entre tools de consulta directa y `command_pipeline` via AgentTool. Presenta los resultados al usuario. Nunca delega la presentación a otro agente.
- `command_pipeline` (SequentialAgent): compuesto por `mitori → shokunin`.
  - `mitori` (LlmAgent con BuiltInPlanner): analiza la petición y genera un JSON `action_plan` con pasos ordenados y asignaciones de agente. Output guardado en `output_key="action_plan"`.
  - `shokunin` (LlmAgent): lee `action_plan` del estado y ejecuta cada paso llamando a los AgentTools especialistas correspondientes.

**Cuándo no usar el pipeline:**
Los agentes conversacionales y de asesoramiento (p.ej. `fertilizer_advisor`, `phytosanitary_advisor`) no usan este patrón. Usan `create_agent` solo con `system_prompt` — sin pipeline de planificación, sin enrutamiento explícito, sin campos de estado. El pipeline está reservado para operaciones de comando que necesitan coordinación multi-agente. Todo lo demás debe ser lo más libre posible (ver `docs/project/vision.md`).

**Consecuencias:**
- sensei tiene una única responsabilidad: enrutar y presentar.
- mitori tiene una única responsabilidad: planificar.
- shokunin tiene una única responsabilidad: ejecutar.
- Las instrucciones de formato y tono viven únicamente en el prompt de sensei.
- Los nodos conversacionales son fáciles de añadir: una llamada a `create_agent` con tools y un prompt.

---

## ADR-003 — Patrón de confirmación: suspensión async del tool

**Estado:** Aceptado

**Contexto:**
Los comandos que modifican datos (crear, actualizar, eliminar, aplicar) requieren aprobación explícita del usuario antes de ejecutarse. La solución debe funcionar dentro del modelo de ejecución de ADK, que ejecuta los agentes hasta completar sin soporte nativo de interrupciones.

**Decisión:**
Los tools de confirmación son funciones `async`. Cuando se necesita aprobación del usuario, el tool:
1. Registra una entrada de respuesta pendiente en `pending_human_responses` (indexada por user ID).
2. Envía el prompt de confirmación (con botones aceptar/cancelar) al usuario via Telegram.
3. Suspende la ejecución con `await asyncio.wait_for(event.wait(), timeout)`.

Mientras el tool está suspendido, el event loop del runner de ADK queda libre. Cuando el usuario responde:
- **Pulsación de botón**: `handle_confirmation_callback` asigna `pending_human_responses[user_id]["response"] = accepted` y llama a `event.set()`.
- **Respuesta de texto**: `handle_user_message` asigna la respuesta y llama a `event.set()`.

El tool se reanuda, lee la respuesta y ejecuta u omite la operación.

Las preguntas abiertas (no binarias aceptar/cancelar) usan `ask_human` siguiendo el mismo patrón, con una respuesta de texto plano en vez de un callback de botón.

Las confirmaciones del mismo usuario se serializan mediante un `asyncio.Lock` por usuario, evitando condiciones de carrera entre confirmaciones simultáneas.

**Consecuencias:**
- Los planes con pasos dependientes funcionan: cada paso bloquea hasta que el usuario responde antes de que se ejecute el siguiente.
- El plan original no se pierde entre confirmaciones — la ejecución se pausa, no termina.
- El diálogo mid-plan es posible via `ask_human`.
- Se aplica un timeout de 5 minutos (`DEFAULT_TIMEOUT_SECONDS`); las confirmaciones sin resolver lanzan `TimeoutError`.

---

## ADR-004 — Gestión de sesión: reset por desbordamiento de eventos

**Estado:** Aceptado

**Contexto:**
El `InMemoryRunner` de ADK acumula eventos en la sesión. Las sesiones largas degradan el rendimiento y pueden alcanzar límites de tokens.

**Decisión:**
Las sesiones se resetean (se eliminan y recrean) cuando `len(session.events) > MAX_SESSION_EVENTS` (actualmente 50). Al resetear, la sesión se recrea solo con el estado de contexto base (`current_date`, `next_saturday`, `user_location`). No se lleva ningún resumen de conversación hacia adelante.

**Consecuencias:**
- La memoria de sesión está acotada; no hay crecimiento ilimitado.
- El contexto conversacional se pierde al resetear — esto es un issue conocido (ISSUE-002).
- 50 eventos se alcanza rápidamente en conversaciones con muchas llamadas a tools (cada tool call genera múltiples eventos).

---

## ADR-005 — Los mensajes de confirmación pertenecen a la capa de presentación

**Estado:** Aceptado

**Contexto:**
Los tools que modifican datos requieren confirmación del usuario antes de ejecutarse. Inicialmente, cada tool contenía una función privada (p.ej. `_build_delete_confirmation`) responsable de formatear el prompt de confirmación — mezclando lógica de dominio con concerns de presentación. También se pasaba un parámetro `summary` generado por el LLM para proveer el texto de confirmación, lo que transfería la responsabilidad de presentación al modelo.

**Decisión:**
Los builders de mensajes de confirmación se inyectan en los tools como `build_confirmation_message: Callable`. Las implementaciones viven en la capa de presentación (`telegram/confirmation_messages.py`). El dominio nunca formatea texto para el usuario. El parámetro `summary` se elimina de todas las firmas de tools.

**Consecuencias:**
- Los tools son testeables en aislamiento usando un builder stub — sin dependencia de formatos de texto específicos.
- Cambiar el idioma o formato de las confirmaciones requiere tocar únicamente la capa de presentación.
- Añadir un nuevo tipo de trabajo requiere un nuevo builder en `telegram/messages/`, no un cambio en el código de dominio.
- El LLM ya no genera el texto de confirmación, eliminando una fuente de no-determinismo en el mensaje al usuario.
