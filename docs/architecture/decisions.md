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
