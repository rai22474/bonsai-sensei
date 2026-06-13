# Decisiones de Arquitectura

## ADR-001 — Continuar con ADK; migración a LangGraph descartada

**Estado:** Decidido. Enmendado por ADR-015 (2026-06-08): la afirmación "ADK no soporta HITL de forma nativa" ya no es válida en ADK 2.0.

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

## ADR-006 — Wiki markdown como base de conocimiento del agente

**Estado:** Aceptado

**Contexto:**
El conocimiento sobre el cultivo de bonsáis (especies, enfermedades, fertilizantes, fitosanitarios) es relacional: las fichas se referencian entre sí. Almacenarlo en campos estructurados de la BD obliga al agente a cruzar datos manualmente y pierde la navegabilidad entre entidades. El patrón "LLM Wiki" de Karpathy propone compilar el conocimiento en páginas markdown persistentes que el LLM edita y consulta directamente.

Referencias: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f, https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2

**Decisión:**
El conocimiento del dominio se almacena como ficheros markdown en disco (`WIKI_PATH`), no como campos estructurados en la BD. La BD solo guarda el path relativo al fichero (`wiki_path`). El agente usa el tool `read_wiki_page` para leer y navegar entre páginas. Los links entre páginas usan la sintaxis `[[ruta/pagina.md]]`; el agente puede seguirlos llamando al tool con esa ruta. Las páginas se generan automáticamente al crear entidades (via Tavily) y pueden actualizarse incrementalmente via el agente.

**Consecuencias:**
- Las fichas son legibles directamente por humanos fuera del sistema (Obsidian, cualquier editor markdown).
- El agente navega relaciones semánticas (especie → enfermedad → fitosanitario) sin lógica especial — solo leyendo links.
- Añadir un nuevo tipo de entidad (enfermedad, estilo de diseño) requiere un nuevo compiler de wiki y un subdirectorio, no cambios de schema.
- Requiere un volumen persistente (`WIKI_PATH`) — no funciona en entornos con filesystem efímero (p.ej. Cloud Run sin volumen montado).
- El endpoint `GET /api/wiki?path=...` expone las páginas para tests de aceptación y lectura externa.

---

## ADR-007 — El compilador de wiki es un agente con runner propio, no una función de plantilla

**Estado:** Aceptado

**Contexto:**
La primera implementación del compilador de wiki usaba una función que lanzaba una consulta Tavily por sección (`## Riego`, `## Luz`...) y volcaba las respuestas en una plantilla fija. Esto no está alineado con el patrón Karpathy: el LLM no sintetiza nada, no decide cuántas búsquedas hacer, no genera wikilinks a entidades relacionadas. La estructura resultante es rígida e igual para todas las especies.

**Decisión:**
El compilador de wiki es un agente ADK con su propio `InMemoryRunner`, independiente del runner del sensei. Usa Tavily como tool de búsqueda y un tool `write_wiki_page` para escribir el fichero en disco. El agente decide qué buscar, cuántas veces, cómo estructurar la ficha y qué wikilinks añadir (`[[../diseases/spider-mite.md]]`). El runner es de sesión única (una sesión por compilación) y se descarta al terminar.

El compilador no pertenece al flujo conversacional (sensei → botanist): es gestión de conocimiento, no interacción con el usuario. Por eso tiene runner propio en lugar de ser un AgentTool del botanist.

**Consecuencias:**
- Las fichas varían según la especie — un junípero y un ficus no tienen por qué tener las mismas secciones.
- El agente puede generar wikilinks a entidades relacionadas si las detecta en las fuentes.
- Los tests del compilador verifican que se creó el fichero y que contiene estructura mínima esperada — no el texto exacto.
- La función `build()` pasa a ser `async`; el confirm tool hace `await wiki_page_builder(...)`.
- Un fallo del compilador no bloquea la creación de la especie — se puede crear sin wiki_path y compilar después.

---

## ADR-008 — La wiki se monta como bind mount en el host, no como volumen Docker

**Estado:** Aceptado

**Contexto:**
La wiki de especies (ADR-006) se almacena en disco en `WIKI_PATH`. Inicialmente se usó un named volume Docker (`wiki_data`), que es opaco: para leer o editar las páginas hay que entrar al contenedor o usar `docker volume inspect`. Dado que el despliegue es en un servidor propio (Ryzen 5) con filesystem persistente, esto supone una fricción innecesaria para revisar o editar fichas desde el host.

**Decisión:**
El wiki se monta como bind mount en `./wiki` (relativo al directorio del compose). El contenedor sigue usando `WIKI_PATH=/app/wiki` — no hay cambio de código. El directorio `./wiki` en el host es accesible directamente con cualquier editor o desde Obsidian.

En el compose de acceptance tests se mantiene un named volume (`wiki_data_acceptance`) porque los datos son efímeros y no necesitan ser accesibles desde el host.

**Consecuencias:**
- Las fichas markdown son editables e inspeccionables directamente en el host sin acceder al contenedor.
- El directorio `./wiki` debe excluirse del repositorio vía `.gitignore` (contiene datos de usuario generados en runtime, no código fuente).
- Requiere que el directorio exista en el host antes del primer `docker compose up` (Docker lo crea automáticamente si no existe).
- No funciona en entornos con filesystem efímero (ya excluidos por ADR-006).

---

## ADR-009 — Tools deterministas con LLM embebido para flujos de pasos fijos

**Estado:** Aceptado

**Contexto:**
Varios flujos del sistema tienen pasos fijos y ordenados donde todos deben ejecutarse sin excepción: recopilar historial del bonsái, leer el plan wiki existente, listar productos disponibles, leer fichas técnicas, razonar y elegir el producto, escribir el plan resultante en la wiki. La implementación inicial usaba un `Agent` LLM con tools (un `fertilizer_advisor`) cuya instrucción decía explícitamente "sigue estos pasos en orden, sin omitir ninguno". El LLM ignoraba el paso de escritura en la wiki con frecuencia porque el paso era presentado como prosa opcional al final del prompt, no como una obligación estructural.

**Señal de alerta:** cuando la instrucción de un agente dice "sigue estos pasos en orden, sin omitir ninguno", es síntoma de que el control debería estar en Python, no en el prompt.

**Decisión:**
Para flujos con pasos fijos y efectos secundarios obligatorios, se usa una **tool determinista** en lugar de un agente con tools:
- Los pasos de recopilación de datos (DB, wiki) se ejecutan en Python de forma garantizada.
- Solo el paso de razonamiento puro (elegir el producto más adecuado dado el contexto) se delega a un LLM via `InMemoryRunner` sin tools — solo entrada de texto, salida de texto/JSON.
- El paso de escritura en wiki se ejecuta en Python después del razonamiento, de forma garantizada.

El `InMemoryRunner` embebido sigue el mismo patrón que ADR-007: sesión propia, aislada del runner conversacional, descartada al terminar.

**Criterio general para elegir entre los dos patrones:**

| Situación | Patrón |
|---|---|
| Pasos fijos, todos obligatorios, efectos secundarios garantizados | Tool determinista + LLM embebido solo para razonamiento |
| El LLM necesita decidir cuántos pasos dar, en qué orden, o si saltarse alguno | Agente con tools |
| Flujo conversacional multi-turno con el usuario | Agente libre sin pipeline |

**Consecuencias:**
- La escritura en wiki está garantizada — ya no depende de que el LLM decida ejecutar el último paso.
- El LLM embebido recibe un contexto completamente ensamblado en Python; si falta un dato, es un bug de código, no una omisión del modelo.
- El `InMemoryRunner` embebido no hereda el estado de la sesión conversacional — el contexto debe ensamblarse explícitamente.
- Si el LLM del paso de razonamiento devuelve JSON malformado, la tool lanza excepción (no escribe una página parcial). El agente orquestador reporta el error.
- Las tools son testeables en aislamiento reemplazando el runner por un stub.

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

---

## ADR-010 — Contrato mitori→sub-agente: Option A adoptada; Option C diferida

**Estado:** Parcialmente decidido (Option A adoptada; Option C diferida pendiente evaluación)

**Contexto:**
El pipeline `mitori → shokunin → AgentTool` (ADR-002) transmite cada paso del plan al sub-agente como un campo `request` en texto natural. Esto produce pérdida de información: los valores concretos del mensaje del usuario (fechas, dosis, nombres) quedan enterrados en lenguaje natural y los sub-agentes los reinterpretan con variabilidad. Se evaluaron tres opciones de corrección:

- **Option A** — enriquecer el JSON del plan con un campo `parameters` (dict) por paso, de forma que mitori incluya los valores estructurados junto al `request` en texto libre.
- **Option B** — schema parcial solo para las acciones de alta frecuencia (aplicar fertilizante, aplicar fitosanitario).
- **Option C** — capa de despacho determinista: mitori elige un `action_type` canónico en lugar de un agente por nombre; un dispatcher Python resuelve el agente y valida el payload antes de invocarlo.

**Decisión:**
Se adopta **Option A** como solución inmediata. El campo `parameters` se añade al schema de `mitori_instruction.j2`; shokunin lo pasa a los sub-agentes junto al `request`. Coste mínimo, sin cambios de contrato entre agentes, compatible con el esquema de instrucciones existente.

**Option C se difiere explícitamente.** La evaluación concluye que Option C resolvería de forma estructural la variabilidad de routing y la dependencia de calibración de descripciones, pero impone costes y riesgos que no están justificados en este momento:
- Requiere definir y mantener un schema por cada `action_type` que mitori delega — alto coste de diseño inicial.
- Añade una capa de routing determinista (dispatcher Python) que va en la dirección opuesta al principio de vision.md de favorecer flexibilidad conversacional frente a control de pipeline.
- Afecta a todos los sub-agentes (caretaker, nursery, botanist, kikaru, etc.) simultáneamente — cambio de alto riesgo sin piloto.

Option B se descarta: el schema parcial introduce inconsistencia de contrato según la acción — peor que Option A (sin schema) y peor que Option C (schema completo).

**Relación con ADRs existentes:**
- Extiende ADR-002: el pipeline mitori/shokunin sigue siendo el mecanismo; solo se enriquece el payload.
- No contradice ADR-009: los tools deterministas con LLM embebido siguen siendo el patrón para flujos de pasos fijos. Option C añadiría determinismo en la capa de despacho, que es un nivel por encima de ADR-009.

**Condiciones para retomar Option C:**
Option C puede retomarse si se observa alguna de estas señales: (a) el routing de mitori falla con frecuencia inaceptable a pesar de Option A y del ajuste de descripciones; (b) se incorpora un nuevo tipo de acción con contrato estricto que hace evidente la necesidad de un dispatcher; (c) el número de `action_type` distintos supera ~10 y la calibración de descripciones se vuelve inmanejable. Ver `docs/project/future-work.md#FUTURE-006` para el plan de implementación al retomar.

**Consecuencias:**
- Los sub-agentes reciben `parameters` como dict validado por mitori, además del `request` en texto libre. La pérdida de información queda resuelta con coste mínimo.
- El contrato sigue siendo semántico: mitori elige el agente por nombre. La calibración de descripciones sigue siendo necesaria.
- El dispatcher Python (Option C) no existe: no hay una capa que valide el contrato entre mitori y sub-agentes en Python. Si mitori genera `parameters` incorrectos, el error se detecta en el sub-agente, no en el punto de despacho.
- Option C queda documentada y evaluada — no se pierde el análisis si las condiciones cambian.

---

## ADR-011 — Los tools gestionan sus propios flujos interactivos en Python, no en el prompt

**Estado:** Aceptado

**Contexto:**
Algunos tools necesitan llevar a cabo múltiples interacciones con el usuario en secuencia antes de completar su operación (p.ej.: confirmar detección de plaga → preguntar si se aplicó tratamiento → seleccionar producto). El enfoque inicial intentaba orquestar estas interacciones desde el prompt del agente: la instrucción decía al LLM que llamase primero a `create_pest_event`, tomase el `pest_event_id` del resultado y luego llamase a `apply_phytosanitary` con ese ID. Este enfoque falló de forma repetida e impredecible: el LLM ignoraba el orden, omitía pasos o llamaba a tools en orden incorrecto.

**Señal de alerta:** cuando la instrucción de un agente dice "llama primero a X, toma el resultado Y, luego llama a Z con Y", es síntoma de que el flujo debe estar en Python **si y solo si** Y es un detalle de implementación que no debería pasar por el LLM (p.ej. un ID de BD generado en el paso anterior). Si X y Z son tools genuinamente independientes y reutilizables por separado, el patrón de dos tools con orquestación LLM puede ser correcto — el síntoma por sí solo no basta. Extensión del principio de ADR-009.

**Decisión:**
Los tools que requieren múltiples interacciones con el usuario gestionan ese flujo íntegramente en Python, usando `ask_confirmation` y `ask_selection` internamente. El LLM solo invoca el tool una vez con los datos que tiene disponibles; el tool suspende y reanuda su ejecución async cuantas veces necesite para completar el flujo.

El flujo interno de un tool multi-paso se organiza en tres fases para eliminar el riesgo de escritura parcial:

**Fase 1 — Recopilar:** todos los `await ask_*` necesarios para tomar decisiones. Sin ninguna escritura a BD.
**Fase 2 — Escribir:** llamar a una función de dominio pura que ejecuta todas las escrituras de una vez. Sin `await ask_*`.
**Fase 3 — Post-write:** interacciones opcionales que no afectan los datos ya escritos (p.ej. proponer revisión de plan). Puede incluir `await ask_*`.

La función de dominio de la Fase 2 se extrae como función privada del módulo (prefijo `_`), sin `ask_*`, testeable e invocable desde cualquier contexto sin UI (batch, tests de dominio, otros agentes).

Ejemplo canónico — `create_pest_event`:
```
Fase 1:
  await ask_confirmation(...)          # confirmar detección

Fase 2:
  record_bonsai_event(...)             # escribe pest_detection
  active_plan = get_active_plan(...)   # consulta sin efecto secundario

Fase 3 (eliminada — ver nota):
  return {"status": "success", "active_plan": bool(active_plan), ...}
  # el LLM menciona el plan activo en texto; no hay ask_plan_review
```

Todo este flujo es Python determinista. El LLM no toma ninguna decisión de orquestación entre pasos.

**Nota — cuándo NO usar `ask_*` dentro del tool (lección de `create_pest_event`):**
La versión original de `create_pest_event` incluía una Fase 3 con `await ask_plan_review(...)` si había un plan activo. Esto se eliminó por dos razones:
1. **Loop de re-registro:** la propuesta era una pregunta Y/N. Si el usuario respondía "sí", mitori re-enrutaba a caretaker, que intentaba registrar la plaga de nuevo.
2. **Timing prematuro:** la propuesta se disparaba antes de que el LLM pudiera ofrecer asesoramiento; el usuario ni siquiera había pedido ayuda todavía.
La solución: el tool devuelve `active_plan: bool` como dato; el LLM lo menciona pasivamente en su respuesta de texto. El usuario inicia la conversación de revisión cuando quiera. Regla derivada: un `ask_*` dentro de un tool solo es apropiado cuando la respuesta es necesaria para completar la escritura a BD de ese mismo tool. Si la información es solo contexto para el siguiente turno del usuario, devuélvela como campo del resultado y deja que el LLM la presente.

**Criterio de aplicación:**

| Situación | Patrón |
|---|---|
| El estado intermedio entre pasos es un detalle de implementación (ID de BD, resultado parcial) que no debe pasar por el LLM | Flujo async en Python dentro del tool |
| El LLM necesita elegir qué tool llamar según el contexto | Agente con tools + descripción de tool bien calibrada |
| Pasos de recopilación + razonamiento + escritura todos obligatorios | Tool determinista con LLM embebido (ADR-009) |
| Dos tools son independientes y reutilizables por separado, aunque en este caso se llamen en secuencia | Dos tools separados; la secuencia la gestiona el LLM |

**Consecuencias:**
- El flujo interactivo multi-paso es 100% determinista — no depende de que el LLM respete un orden descrito en prosa.
- La tool puede reutilizar datos intermedios (p.ej. `pest_event_id`) sin pasarlos por el LLM.
- El `accept_confirmation` del API debe hacer polling hasta encontrar el siguiente estado pendiente (confirmación, selección o revisión de plan) para devolverlo al cliente en la misma respuesta HTTP — evita un round-trip extra.
- Los flujos condicionales (p.ej. solo preguntar por tratamiento si existen productos) son lógica Python, no instrucciones al LLM.
- **Reusabilidad:** la función de dominio de la Fase 2 es independiente del flujo interactivo — testeable y reutilizable sin UI. El workflow (Fases 1+3) es el único sitio que mezcla interacción con orquestación.
- **Sin escritura parcial:** la separación en fases garantiza que ninguna escritura a BD ocurre antes de que el usuario haya tomado todas las decisiones. Si el usuario abandona en la Fase 1, no queda nada escrito. Si falla la Fase 2 a mitad (p.ej. dos escrituras y la segunda lanza excepción), sí puede haber inconsistencia — eso es un problema de transacción de BD, no de este patrón.
- **Testing:** la función de dominio (Fase 2) se testea sin ningún mock de `ask_*`. El workflow completo se testea con mocks de `ask_*` que devuelven respuestas predefinidas en secuencia — más complejo que un tool atómico, pero la función de dominio cubre los casos de escritura de forma simple.
- **Tensión con ADR-005:** ADR-005 establece que el dominio no formatea texto para el usuario (los builders se inyectan). Este ADR extiende esa separación al *cuándo* interactuar: el tool decide el momento y la condición de cada `ask_*`, lo que mezcla lógica de dominio con orquestación de presentación. Se acepta esta tensión porque la alternativa (orquestación via prompt) tiene un coste mayor en fiabilidad.

---

## ADR-012 — Shokunin como BaseAgent determinista, no LlmAgent

**Estado:** Aceptado

**Contexto:**
`shokunin` era un `LlmAgent` que leía `action_plan` del estado de sesión y llamaba a los AgentTools de los sub-agentes. El LLM hacía de capa de routing: interpretaba el JSON del plan y decidía qué AgentTool invocar para cada paso. Este diseño tenía tres problemas:

1. **Coste:** 2 LLM calls extra por paso de plan (entrada + salida del LLM de routing). Medido: ~72s para una operación de un solo paso.
2. **No-determinismo:** el LLM podía alucinar el agente destino, reordenar pasos o ignorar parámetros — introduciendo variabilidad donde el comportamiento debía ser mecánico.
3. **No testeable:** un `LlmAgent` no tiene superficie pública que se pueda unit-testear sin el runner completo de ADK.

**Señal de alerta** (extensión de ADR-009/ADR-011): si un agente recibe un JSON estructurado y su única función es iterar sobre él e invocar los elementos que encuentra, el LLM es overhead puro. No hay razonamiento, solo traducción — y esa traducción debe estar en Python.

**Decisión:**
`shokunin` se reimplementa como `Shokunin(BaseAgent)` — un agente determinista sin LLM. El método público `execute(ctx: InvocationContext) -> list[Event]` implementa el bucle de ejecución:

1. Lee `action_plan` del estado de sesión y lo parsea como JSON.
2. Ordena los pasos por `order`.
3. Por cada paso: resuelve el `AgentTool` por nombre, construye el `request` concatenando `request` + `parameters`, llama a `agent_tool.run_async(...)`.
4. Si el resultado contiene `{"status": "cancelled"}` o `{"status": "error"}`, detiene la ejecución (no ejecuta pasos siguientes).
5. Si el agente no está registrado, registra el error y continúa (no detiene el plan).
6. Si `run_async` lanza una excepción, la convierte a `{"status": "error", "message": str(exc)}` — nunca propaga.
7. Serializa todos los resultados como `execution_result` en el estado de sesión.

`_run_async_impl` (hook requerido por `BaseAgent`) solo delega a `execute` y convierte la lista en un generador async.

**Bugs corregidos respecto al LlmAgent original:**
- `_is_terminal` usaba string matching frágil (`'"status": "cancelled"' in result`) — no detectaba `"error"` y fallaba con variaciones de formato JSON. Reemplazado por `json.loads` + `result.get("status") in ("cancelled", "error")`.
- `_execute_step` no tenía try/except — una excepción en `AgentTool.run_async` propagaba como crash sin registrar el fallo del paso.

**Consecuencias:**
- **Velocidad:** ~72s → ~19s para operaciones de un paso. El ahorro escala linealmente con el número de pasos del plan.
- **Determinismo:** el routing mitori→sub-agente es 100% determinista. El único LLM que razona sobre el plan es mitori (que lo genera). Shokunin solo lo ejecuta.
- **Testeable:** `execute(ctx)` es un método público cubierto por 24 unit tests que verifican todos los caminos de error sin necesidad del runner de ADK.
- **Error handling explícito:** los estados terminales (`cancelled`, `error`) detienen el plan de forma controlada. Los agentes no registrados no detienen el plan — el error queda en `execution_result` para que sensei lo presente al usuario.
- **Compatibilidad:** `AgentTool.run_async` preserva el `user_id` de la sesión padre → las confirmaciones async (`ask_confirmation`, `ask_human`) siguen funcionando correctamente desde los sub-agentes invocados por shokunin.
- **Relación con ADR-002:** la responsabilidad de shokunin sigue siendo "ejecutar el plan de mitori". Solo cambia la implementación: de LLM a Python determinista.

---

## ADR-013 — Índice semántico de wiki con embeddings (FUTURE-002)

**Estado:** Supersedido por ADR-014 (2026-06-05)

**Contexto:**
Los agentes no podían encontrar páginas wiki creadas por el dreamer porque no están registradas en la base de datos. Al mismo tiempo, cargar todas las páginas añade ruido innecesario. FUTURE-002 proponía un índice con embeddings para búsqueda semántica.

**Decisión:**
Índice plano (no grafo) de embeddings en `wiki-index/`, un JSON por página, búsqueda top-k por similitud coseno en memoria con numpy.

**Estructura:**
```
wiki-index/<page_path>.json  →  {page_path, abstract, links, embedding}
```

**Modelo de embedding:** `gemini-embedding-001` (3072 dims). `text-embedding-004` no disponible con la API key usada — descubierto en producción; `gemini-embedding-001` es el equivalente disponible.

**Patrón de dependencias:** todas las funciones del paquete `wiki_index/` siguen el patrón DI del proyecto — los colaboradores (embed callable, load_entries callable) se inyectan, nunca se instancian internamente. `create_embed_text(api_key)` crea el cliente una vez; `create_search_wiki_knowledge_tool(embed, search_index)` recibe ambas funciones.

**Diferencias respecto al diseño de FUTURE-002:**
- El traversal por grafo (seguir links con poda) no está implementado — la búsqueda es plana sobre todos los embeddings. Suficiente para <500 páginas (microsegundos).
- Los sub-agentes (kikaru, kantei, etc.) no usan el índice — solo sensei tiene `search_wiki_knowledge`. Los context builders siguen cargando páginas específicas desde la BD.
- `wiki-index/` en `.gitignore` — se trata como caché regenerable.

**Integración:**
- Dreamer y wiki editor actualizan el índice automáticamente al escribir páginas (en el commit hook post-run).
- Sensei tiene `search_wiki_knowledge` como tool directa; la instrucción lo guía a usarla para preguntas de conocimiento antes de responder.
- Bot admin: `/index` reconstruye el índice completo. REST: `POST /api/wiki/index/rebuild`.

**Consecuencias:**
- El sensei puede encontrar y usar páginas wiki que el dreamer creó, sin depender de la BD.
- Páginas con abstract vacío se omiten del índice (guard en indexer).
- El índice se puede reconstruir desde cero en cualquier momento sin pérdida de datos — es solo caché de los `.md`.
- No hay índice global que gestionar: cada página actualiza su propio JSON.

---

## ADR-014 — Índice wiki migrado a FalkorDB (FUTURE-004)

**Estado:** Implementado (2026-06-05). Supersede ADR-013.

**Contexto:**
ADR-013 almacenaba embeddings en `wiki-index/<page_path>.json` y calculaba similitud coseno en memoria con numpy. Funcional para <500 páginas, pero sin soporte para traversal por grafo. FalkorDB ya corre en producción para `episodic_memory` — coste operacional cero para añadir un segundo grafo.

**Decisión:**
El índice wiki se migra a FalkorDB usando un grafo separado (`WIKI_INDEX_GRAPH=wiki_index`). Un nodo `WikiPage` por página; relaciones `[:LINKS_TO]` entre páginas enlazadas. Vector index nativo sobre `embedding` (3072 dims, cosine).

**Schema:**
```cypher
(:WikiPage {page_path, abstract, embedding: vecf32[3072]})
(:WikiPage)-[:LINKS_TO]->(:WikiPage)

CREATE VECTOR INDEX FOR (n:WikiPage) ON (n.embedding)
  OPTIONS {dimension: 3072, similarityFunction: 'cosine'}
```

**Patrón DI:** `falkordb.Graph` se inyecta como dependencia en todas las funciones del paquete `wiki_index/` siguiendo el patrón del proyecto. Las factories `create_save_entry(graph)`, `create_search_by_embedding(graph)` etc. encapsulan el grafo y devuelven callables. El grafo se construye una vez en `lifespan` de `main.py` y se enlaza via `app.state`.

**KNN:** `CALL db.idx.vector.queryNodes('WikiPage', 'embedding', $k, vecf32($embedding))` — sustituye el loop numpy. FalkorDB devuelve distancia coseno (0=idéntico); el searcher convierte a similitud (`1 - score`) para mantener el contrato público.

**Traversal (FUTURE-002, pendiente):** una vez en FalkorDB, el traversal es una query Cypher de una línea:
```cypher
CALL db.idx.vector.queryNodes('WikiPage', 'embedding', 5, vecf32($embedding))
YIELD node AS seed, score
MATCH (seed)-[:LINKS_TO*1..2]->(related:WikiPage)
WHERE NOT related.page_path IN [seed.page_path]
RETURN DISTINCT related.page_path, related.title
ORDER BY score DESC LIMIT 10
```

**Consecuencias:**
- `numpy` eliminado del paquete `knowledge_base`.
- `wiki-index/` en disco desaparece — el índice vive en FalkorDB.
- `knowledge_base` service depende de `falkordb` en `docker-compose.yml`.
- `initialize_schema(graph)` se llama en `lifespan`; maneja idempotencia capturando `ResponseError("already indexed")`.
- `save_entry` y `search_by_embedding` son callables ligados al grafo, propagados via DI a dreamer, wiki_editor, admin_bot y api.
- Los unit tests usan `MagicMock` para `falkordb.Graph` — sin dependencia de FalkorDB real en tests.

---

## ADR-015 — Migración a ADK 2.0: Dynamic Workflows y RequestInput para HITL iterativo

**Estado:** Decidido (2026-06-08). Enmienda ADR-001.

**Contexto:**
ADR-001 rechazó LangGraph's `interrupt()` porque imponía graph wiring estricto. La solución alternativa fue la suspensión async de tools (ADR-003), que funciona para confirmaciones simples pero tiene dos defectos en flujos de propuesta iterativos (crear plan → criticar → refinar → repetir hasta confirmar):

1. `_MAX_ITERATIONS = 5` en el `LoopAgent` impone un techo artificial — si el usuario necesita más de 5 rondas de crítica, el plan se cancela silenciosamente.
2. El draft vive únicamente en el `InMemoryRunner` privado del runner de propuesta. Un crash entre iteraciones pierde el borrador sin posibilidad de recuperación.

Al migrar a ADK 2.0, se descubrió que los **Dynamic Workflows** (nuevo en 2.0) resuelven exactamente estos dos problemas sin introducir la rigidez de grafo que llevó a rechazar LangGraph.

**Decisión:**
Migrar los runners de propuesta y clarificación (`plan_proposal_runner.py`, `clarification_runner.py`) a ADK 2.0 Dynamic Workflows con `RequestInput`. El patrón `LoopAgent` + `asyncio.Event` (ADR-003) se mantiene para confirmaciones simples de tools individuales (`delete_bonsai`, `create_fertilizer`, etc.) — esos tools son interacción única y no se benefician de checkpointing.

**Por qué Dynamic Workflows y no static Graph Workflows:**
Los static Graph Workflows requieren enumerar todas las transiciones como `edges` explícitas. Los Dynamic Workflows usan control de flujo Python ordinario (`while`, `if/else`, `await`): el ciclo propuesta→`RequestInput`→confirmar/refinar es un `while True` en Python. No hay rigidez de aristas. El criterio de rechazo de ADR-001 (graph wiring estricto) no aplica a Dynamic Workflows.

**Mecanismo de `RequestInput`:**
`RequestInput` pausa el workflow a nivel de framework, no via `asyncio.Event`. El runner emite un evento `adk_request_input` con un `interrupt_id`. Para reanudar, el caller envía un nuevo turn cuyo `new_message` contiene un `FunctionResponse` con ese `interrupt_id`. Un mensaje de texto plano inicia una nueva invocación — no reanuda el workflow suspendido.

**Impacto en la capa de integración Telegram/REST:**

Ficheros que cambian:
- `advisor.py` — `_generate_advise` debe detectar el evento `adk_request_input` y surfacear el `interrupt_id` al caller en lugar de seguir el loop normal.
- `api/advice.py` — los endpoints de interrupción actuales (`/confirmations/{id}/accept`, `/text-response`, etc.) se reemplazan por un único endpoint que construye el `types.Content` con `FunctionResponse` keyed en el `interrupt_id` y llama `advisor(...)` con él.

Ficheros que NO cambian:
- El patrón de llamada `runner.run_async(user_id, session_id, new_message)` — igual que ahora.
- Gestión de sesión, detección de sesión obsoleta, flujo de upload de fotos.
- El handler de Telegram — sigue enviando mensajes y recibiendo respuestas.

**ResumabilityConfig y durabilidad entre reinicios:**
ADK 2.0 ofrece `ResumabilityConfig` para replay de sub-agentes completados tras un crash. Requiere `DatabaseSessionService` (PostgreSQL). El proyecto usa `InMemorySessionService` hoy — esta mejora queda diferida. La migración a Dynamic Workflows mejora ya el problema de las 5 iteraciones y la transparencia del draft sin necesitar `DatabaseSessionService`.

**Consecuencias:**
- El techo de 5 iteraciones desaparece — el loop de crítica puede ser tan largo como el usuario necesite.
- El draft se puede escribir en el estado de sesión exterior en cada ronda de `RequestInput`, dando visibilidad y base para recuperación futura.
- El patrón ADR-003 (`asyncio.Event`) queda como mecanismo para confirmaciones simples únicamente. No se elimina — se limita a su caso de uso correcto.
- ADR-001 queda enmendado: la afirmación "ADK no soporta HITL de forma nativa" ya no es válida en ADK 2.0.
- Trabajo futuro: cuando se añada `DatabaseSessionService`, combinar con `ResumabilityConfig` para durabilidad completa entre reinicios de proceso.

**Referencia de implementación:**
- `bonsai_sensei/src/bonsai_sensei/domain/services/cultivation/plan/plan_proposal_runner.py` — reescribir como Dynamic Workflow
- `bonsai_sensei/src/bonsai_sensei/domain/services/cultivation/plan/clarification_runner.py` — ídem
- `bonsai_sensei/src/bonsai_sensei/domain/services/advisor.py` — detectar `adk_request_input`
- `bonsai_sensei/src/bonsai_sensei/api/advice.py` — unificar endpoints de respuesta bajo `FunctionResponse`

---

## ADR-016 — Canales: routing multi-turno y contexto de sub-agentes en ADK

**Estado:** Implementado (2026-06-13)

**Contexto:**
El agente kiroku necesita gestionar sesiones conversacionales multi-turno: el usuario envía varios mensajes (preguntas, fotos, comentarios) antes de cerrar. ADK 2.0 no tiene soporte nativo para que un sub-agente tome el control del canal durante múltiples turnos consecutivos, ni mecanismo estándar para pasarle contexto de inicialización.

**Decisión — Routing multi-turno (canal custom):**
Cada canal tiene su propio `Runner` ADK y su propia sesión (`session_id = f"{user_id}:kiroku"`). `_generate_advise` lee `active_channel` del estado de la sesión principal y enruta el mensaje al runner del canal activo. El canal se activa cuando un tool escribe `active_channel = "kiroku"` en estado, y se desactiva cuando otro tool escribe `active_channel = None`. Tras cada turno, `_handle_channel_transition` detecta el cambio e invoca los callbacks `on_enter` / `on_exit`.

La sesión separada da al canal historial de conversación propio — no contamina el historial de sensei.

**Decisión — Contexto del sub-agente: dos capas independientes:**

ADK ofrece un único mecanismo documentado para datos persistentes entre turnos: `tool_context.state`. No hay API para "pasar contexto al activar un sub-agente". A partir de esa restricción se establecieron dos capas con responsabilidades distintas:

*Capa 1 — Datos de dominio para tools (session state):*
`start_work_documentation` escribe los identificadores de la sesión en el estado del canal: `kiroku_work_id`, `kiroku_work_type`, `kiroku_bonsai_name`, `kiroku_session_type`, y el acumulador `kiroku_photo_analyses`. Los tools los leen directamente de `tool_context.state`. El mínimo de estado es el que no puede derivarse en runtime: `work_id` (clave de BD), nombres para display (`bonsai_name`, `work_type`), tipo de sesión, y el acumulador de análisis de fotos. Todo lo demás (bonsai_id, user_id, session_date, photo_count) se deriva en el momento de uso desde la BD o se computa.

*Capa 2 — Contexto para el LLM (instruction injection):*
Los valores de sesión se inyectan en `KIROKU_INSTRUCTION` via variables de estado de ADK (`{kiroku_bonsai_name?}`, `{kiroku_work_type?}`, `{kiroku_session_type?}`, `{kiroku_work_id?}`). Esto permite que el LLM pase `work_id` y `session_type` como parámetros explícitos a los tools — el LLM los lee de su instrucción y los pasa, en lugar de que los tools los lean de state. Sin esta inyección el LLM ignora el contexto de sesión y pide clarificación al usuario.

La regla resultante: **state para acumuladores y para inyectar contexto en la instrucción; parámetros LLM para lo que el LLM puede pasar directamente desde su contexto**.

**Tensión aceptada:**
`start_work_documentation` hace dos cosas: seleccionar el trabajo (dominio) y activar el canal escribiendo estado (routing). ADK no ofrece separación nativa de estas responsabilidades. La alternativa — inyectar el contexto vía un mensaje `[sistema]` en el `on_enter` callback — requeriría dar al callback acceso al runner del canal y costaría un LLM call extra de inicialización. No vale el coste.

**Separación domain/lifecycle en los tools del canal:**
- `document_work_session`: genera y escribe la wiki. Lógica de dominio pura; no toca estado del canal.
- `close_work_session`: cierra el canal (limpia state, escribe `channel_handoff_summary`, setea `active_channel=None`). Separado de `document_work_session` porque son responsabilidades distintas: una es dominio, la otra es ciclo de vida del canal.

**Consecuencias:**
- Multi-turno funciona de forma transparente; el canal persiste hasta que `close_work_session` lo libera.
- Minimizar el estado del canal reduce acoplamiento: cuanto menos estado, menos riesgo de inconsistencia entre sesión principal y sesión del canal.
- Si ADK añade soporte nativo para canales o contexto de activación, el mecanismo custom puede simplificarse sin cambiar los tools ni la instrucción.
- El acumulador `kiroku_photo_analyses` no tiene alternativa en state: una lista que crece durante la sesión no puede pasarse como parámetro LLM (demasiado grande; no es fiable que el LLM la gestione íntegra).
