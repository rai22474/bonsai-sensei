# Trabajo futuro

Iniciativas pendientes que aún no están listas para implementar. Consultar antes de empezar tareas relacionadas.

---

## FUTURE-015 — Migrar runners de propuesta a ADK 2.0 Dynamic Workflows (ADR-015) ✅ Implementado (2026-06-08)

**Contexto:**
Los runners de propuesta de planes (`plan_proposal_runner.py`, `clarification_runner.py`) usan `LoopAgent` + `asyncio.Event` (ADR-003). Tienen dos defectos: límite de 5 iteraciones que cancela silenciosamente el plan si el usuario hace más rondas de crítica, y pérdida del borrador si el proceso se reinicia. ADR-015 (2026-06-08) documenta que ADK 2.0 Dynamic Workflows con `RequestInput` resuelven ambos sin introducir la rigidez de grafo que llevó a rechazar LangGraph (ADR-001).

**Diseño:**
- Reemplazar el `LoopAgent` interno de ambos runners por un Dynamic Workflow con `while True` en Python y `RequestInput` en lugar de `asyncio.Event`.
- `RequestInput` pausa a nivel de framework y emite un `interrupt_id`. La capa REST (`advice.py`) detecta el evento `adk_request_input`, lo surfacea al caller, y cuando el usuario responde construye un `FunctionResponse` keyed en ese `interrupt_id`.
- El draft se escribe en el estado de sesión exterior en cada ronda antes de pausar.
- El patrón ADR-003 se mantiene para confirmaciones simples de tools individuales.

**Dependencia de infraestructura diferida:** `DatabaseSessionService` (PostgreSQL) para `ResumabilityConfig` y durabilidad entre reinicios. No es necesaria para el fix del límite de iteraciones.

**Ficheros afectados:**
- `plan_proposal_runner.py`, `clarification_runner.py` — reescribir como Dynamic Workflow
- `advisor.py` — detectar `adk_request_input`, surfacear `interrupt_id`
- `api/advice.py` — unificar endpoints de respuesta bajo `FunctionResponse`

**Fase 1 implementada (2026-06-08):** `LoopAgent` (deprecated) eliminado de ambos runners. `plan_proposal_runner.py`: `LlmAgent` directo + draft state en sesión exterior. Fija el bug de cancelación silenciosa.

**Fase 2 implementada (2026-06-08):** `clarification_runner.py` migrado a ADK 2.0 `Workflow + @node(rerun_on_resume=True) + LlmAgent(output_schema=ClarificationAction)`. El LLM retorna JSON estructurado en lugar de llamar tools. Bridge loop en Python: detecta `adk_request_input` → llama `ask_human`/`ask_poll` → resume con `FunctionResponse`. Los 3 templates de clarificación actualizados al nuevo esquema JSON.

**Prototipo verificado (2026-06-08):** `run_async + FunctionResponse(interrupt_id)` reanuda el workflow correctamente. Patrón confirmado:
- `@node(rerun_on_resume=True)` obligatorio en nodos con `RequestInput`
- En el nodo: `resume = ctx.resume_inputs.get(interrupt_id)` — el nodo se re-ejecuta desde el inicio, no hay `send()` al generador
- Estado entre nodos: `ctx.state["key"]`, no `ctx.session.state["key"]`
- `advice.py` detecta evento con `has_request_input_function_call(event)`, surfacea `interrupt_id` al caller; Turn 2 construye `Content(parts=[create_request_input_response(interrupt_id, {"result": user_text})])` y llama `run_async` normalmente

**Fase 3 (2026-06-08):** `manage_plan.py` y `design/manage.py` migrados a ADK 2.0 Static Graph Workflow con nodos `validate_and_load_context → clarify_objectives → propose_plan → create_plan`. Routing condicional vía `ctx.route = "ok"|"confirm"|"reclarify"` + routing maps `{"ok": next_node, ...}`. Tests unitarios: 11/11 verdes.

**Nota de implementación:** En ADK 2.0 `FunctionNode`, el retorno de la función va a `ctx.output` (no a `ctx.route`). El routing condicional requiere `ctx.route = "value"` explícito — nunca `return "value"`. Las routing maps `(from_node, {"route": to_node})` solo disparan cuando el nodo emite ese route. Edges incondicionales `(A, B)` (route=None) siempre disparan.

**Pendiente diferido:** `DatabaseSessionService` para durabilidad entre reinicios. No bloquea el comportamiento actual.

---


## FUTURE-012 — Plan de desarrollo artístico del bonsai

**Contexto:**
El sistema gestiona fertilización y fitosanitarios pero carece de la dimensión artística: fase de desarrollo, objetivo de diseño, estilo y calendario de trabajos técnicos estacionales (alambrado, defoliación, pinzamiento, poda de estructura...). Esta iniciativa añade el `DevelopmentPlan` como tercer tipo de plan junto a `FertilizationPlan` y `PhytosanitaryPlan`.

### Entidad `DevelopmentPlan`

```
DevelopmentPlan
  id
  bonsai_id            FK → bonsai
  development_path     str  ("planton", "yamadori", "vivero", "nebari")
  current_phase        str  ("engorde", "aclimatacion", "estructura", "refinamiento", ...)
  target_style         str  slug de wiki design/ (ej. "kengai", "bunjin", "moyogi")
  design_goal          str  texto libre ("dar movimiento al primer tramo")
  status               str  ("active" | "abandoned")
  wiki_path            str  bonsai/<slug>/design-plans/<periodo>.md
  created_at
  abandoned_at
  abandonment_reason
```

`PlannedWork` gana FK `development_plan_id → developmentplan.id` (nullable, SET NULL on delete).

### Trabajos del plan

Cada trabajo es un `PlannedWork` con:
- `work_type` = slug de técnica de wiki (ej. `"defoliacion"`, `"alambrado"`)
- `development_plan_id` = id del plan
- `payload` = `{"technique_name": str, "wiki_path": str, "notes": str}`

Las técnicas salen de `techniques/` en la wiki (knowledge_base FUTURE-003 ya implementado). Si el LLM propone una técnica nueva, el usuario la valida y pasa a la wiki.

### Flujo conversacional

Kikaru gestiona tres nuevas herramientas:
- `manage_development_plan(bonsai_name, start_date, end_date, development_path, current_phase, target_style, design_goal)` — crea o reemplaza el plan activo. Ciclo: clarificación (estado del árbol, restricciones) → propuesta de calendario estacional → confirmación → persistencia.
- `abandon_development_plan(bonsai_name, reason)` — abandona el plan activo.
- `evaluate_development_plan(bonsai_name)` — evalúa si el plan activo sigue siendo válido dado el estado actual del árbol.

### Contexto del LLM al generar el plan

El prompt de propuesta recibe:
- Especie: wiki `species/<slug>.md` (técnicas adecuadas, ventanas estacionales)
- Estilo objetivo: wiki `design/<target_style>.md`
- Fase y camino: texto estructurado
- Historial de eventos del árbol
- Localización del usuario (para calcular fechas concretas desde ventanas estacionales)
- Plan existente si hay (será abandonado)

### Fertilización: sin cambios estructurales

La dependencia es suave: el LLM leerá la wiki del DevelopmentPlan cuando genere o evalúe un plan de fertilización (vía MCP), igual que ya lee `goal` y eventos.

### Archivos nuevos

- `domain/development_plan.py` — entidad SQLModel
- `domain/development_plan_store.py` — CRUD
- `alembic/versions/*_add_development_plan.py`
- `alembic/versions/*_add_development_plan_id_to_planned_work.py`
- `api/development_plans.py` — REST CRUD para tests de aceptación
- `services/cultivation/plan/design/manage.py`
- `services/cultivation/plan/design/abandon_plan.py`
- `services/cultivation/plan/design/evaluate.py`
- `services/cultivation/plan/design/factory.py`
- `services/cultivation/plan/design/templates/` (clarification, proposal, wiki page, index)
- `telegram/messages/planning_messages.py` — extensión con mensajes de design plan

### Archivos modificados

- `domain/planned_work.py` — añadir `development_plan_id`
- `domain/cultivation_plan.py` — añadir `delete_future_planned_works_by_development_plan`
- `services/cultivation/plan/kikaru.py` — nueva sección + nuevos params de tool
- `services/cultivation/plan/factory.py` — wiring de nuevas herramientas
- `services/factory.py` y `agents_factory.py` — propagación de nuevos callables
- `main.py` — registrar router de development_plans

### Punto de partida al retomar

1. Crear `DevelopmentPlan` + store + migraciones.
2. Añadir FK `development_plan_id` a `PlannedWork` + migración.
3. Crear `api/development_plans.py` con DELETE para cleanup de tests.
4. Implementar `design/manage.py` sin reutilizar `create_manage_plan_tool` (no hay catálogo de productos; las técnicas vienen de la wiki).
5. Añadir `abandon_plan` y `evaluate` siguiendo el patrón de fertilización.
6. Ampliar kikaru y factory.
7. Tests de aceptación BDD.

---

## FUTURE-006 — Option C: despacho determinista entre agentes

**Contexto:**
La evaluación de esta opción, la comparación con Option A (adoptada en FUTURE-005) y Option B (descartada), y las condiciones bajo las cuales retomar esta iniciativa están registradas en ADR-010 (`docs/architecture/decisions.md`).

### Punto de partida al retomar

1. Inventariar todas las `action_type` que mitori delega actualmente.
2. Evaluar si Option B (schema parcial solo para acciones de alta frecuencia) es suficiente.
3. Decidir si el contrato se valida con Pydantic en el dispatcher o con JSON Schema en la instrucción de mitori.
4. Implementar en una acción piloto (e.g., `apply_fertilizer`) antes de generalizar.

**Dependencia:** Ninguna — puede retomarse independientemente de FUTURE-004.

---

## FUTURE-009 — Memoria de estrategias para mitori

**Contexto:**
Mitori genera un plan JSON en cada invocación desde cero. Para peticiones similares que ya han tenido éxito, debería recuperar el patrón de plan anterior y reutilizarlo como referencia, reduciendo errores de routing y mejorando la consistencia.

**Diseño:**

Pipeline actual: `[mitori, shokunin]`
Pipeline propuesto: `[StrategyRecaller, mitori, shokunin, StrategySaver]` (cuando mem0 disponible)

**`StrategyRecaller`** (`BaseAgent` sin LLM):
- Extrae el último mensaje de usuario de `ctx.session.events`
- Busca en mem0 con `filters={"user_id": ..., "agent_id": "mitori_strategies"}`, `top_k=1`
- Si encuentra resultado: escribe `ctx.session.state["recalled_strategy"]` con el texto formateado (sección con header + contenido + instrucción de adaptación)
- Si no: no escribe nada (estado ausente = sin estrategia previa)

**`StrategySaver`** (`BaseAgent` sin LLM):
- Lee `execution_result` y `action_plan` de session state
- Si algún step tiene `status: error|cancelled` → no guarda
- Si todo OK → llama `mem0.add([{"role": "assistant", "content": "Para el objetivo '...', el plan exitoso fue: {...}"}], user_id=..., agent_id="mitori_strategies")`

**Inyección en mitori:**
Añadir `{recalled_strategy?}` en `mitori_instruction.j2` entre la sección de herramientas disponibles y `# Comportamiento`. ADK sustituye el placeholder desde session state en tiempo de ejecución. Si vacío, no aparece nada.

**Condicionalidad:**
`StrategyRecaller` y `StrategySaver` solo se añaden al pipeline si `mem0_client is not None`. Sin `DATABASE_URL`, el pipeline no cambia.

**Propagación de `mem0_client`:**
`__init__.py` crea `mem0_client` antes de llamar a `create_sensei_agent` → `agents_factory.py:create_sensei_agent(mem0_client=...)` → `factory.py:create_sensei_group(mem0_client=...)`.

**Nota sobre `async def _run_async_impl`:**
Ambos agentes son pure side-effect (no yieldan eventos). Para que Python los trate como async generators (requerido por ADK), usar el patrón `if False: yield` al final del body.

**Archivos afectados:**
- `bonsai_sensei/domain/services/strategy_memory.py` (nuevo)
- `bonsai_sensei/domain/services/templates/mitori_instruction.j2`
- `bonsai_sensei/domain/services/factory.py`
- `bonsai_sensei/domain/services/agents_factory.py`
- `bonsai_sensei/__init__.py` (mover creación de mem0_client antes de `create_sensei_agent`)

---

## FUTURE-011 — Generación de imágenes de referencia para el plan de diseño

**Contexto:**
El agente de plan de diseño (FUTURE-010) produce un texto con técnicas y ventanas temporales. Para objetivos visuales ("afinar ápice", "dar movimiento al primer tramo") una imagen de referencia aporta información que el texto no puede transmitir. El usuario necesita ver, no solo leer.

**Dos sub-opciones a evaluar:**

**Opción A — Imagen de referencia estética** (recomendada como punto de partida):
- Tool `generate_design_image(description, bonsai_id)` en el agente de plan de diseño
- Llama a Imagen API con un prompt construido a partir del objetivo + especie + estilo
- Guarda resultado en `gallery/design-references/`
- El agente incrusta la referencia en el wiki plan (`design-plan.md`) como imagen inline
- Mínimo código nuevo; máxima libertad conversacional; misma lógica que Opción B del dominio (wiki first)

**Opción B — Diagrama técnico anotado sobre foto real** (segunda iteración si Opción A valida el flujo):
- El agente recupera la foto más reciente del árbol desde galería
- Envía foto + descripción de técnica a Gemini multimodal
- Gemini devuelve imagen con marcas superpuestas (dirección de alambre, cortes de poda)
- Más útil para el usuario; más complejo; requiere que el árbol tenga fotos en galería

**Recomendación:** Implementar Opción A primero. Migrar a Opción B si la referencia estética resulta insuficiente o si el usuario pide anotaciones sobre su árbol real.

**Dependencia:** FUTURE-010 debe estar implementado (el agente de plan de diseño es el host natural de este tool).

---

## FUTURE-013 — Soporte multi-usuario ✅ Implementado (2026-06-07)

**Nota de implementación:**
- Se reutilizó `user_settings` (PK = `telegram_user_id`) como identidad de usuario en lugar de crear una entidad `User` separada. El `user_id` en sesión ADK es el `telegram_user_id` raw, que coincide con el PK de `user_settings`. FUTURE-014 debe tener en cuenta que no hay UUID interno — la referencia de colección será `user_settings.user_id`.
- `user_id` añadido como FK a `bonsai`, `fertilizer`, `phytosanitary` (migración `k2l3m4n5o6p7`). Todos los tools del sensei y del storekeeper resuelven `user_id` desde `tool_context` y lo aplican en lookups y creaciones.
- `wiki_path` de entidades de usuario usa prefijo `users/{user_id}/bonsai/` en todos los builders (bonsái, planes, informes kantei). Almacén de fotos del sensei también usa `{user_id}/{slug}/`.
- FalkorDB: nodos `WikiPage` llevan `user_id`; búsqueda KNN filtra `global-only` o `global+user` según contexto.
- Observations pipeline: observaciones del usuario siempre van a zona `users/{user_id}/`; nunca se promueven a wiki global.
- `user_settings` se crea automáticamente al primer mensaje Telegram. La REST API no auto-crea — los tests de aceptación usan fixture `setup_user_settings` en root conftest para garantizar la FK antes de crear entidades.

**Contexto:**
El sistema asume implícitamente un único usuario: los bonsáis no tienen FK de usuario en BD, y los `wiki_path` usan `bonsai/<slug>/` sin namespace de usuario — lo que produce colisiones si dos usuarios tienen árboles con el mismo slug. Esta iniciativa establece la base de identidad de usuario que habilita tanto el aislamiento de datos como la futura multi-colección (FUTURE-014).

### Cambios en BD

```
User
  id
  telegram_user_id    unique
  location            str (nullable)
  created_at

Bonsai
  user_id    FK → User    ← nuevo (nullable en migración, backfill con usuario único actual)
```

Alembic migrations:
1. `create_user_table`
2. `add_user_id_to_bonsai` — nullable, backfill con el ID del usuario existente, luego NOT NULL

### Cambio de convención de wiki_path

Todos los builders que construyen `wiki_path` para entidades de usuario deben usar el prefijo `users/{user_id}/`:

```
# Antes
bonsai/<slug>/
bonsai/<slug>/fertilization-plans/
bonsai/<slug>/design-plans/

# Después
users/{user_id}/bonsai/<slug>/
users/{user_id}/bonsai/<slug>/fertilization-plans/
users/{user_id}/bonsai/<slug>/design-plans/
```

El conocimiento general (dreamer/keeper) sigue en `species/`, `techniques/`, `diseases/` — sin cambio.

**Este cambio debe hacerse antes de que haya datos de producción reales.** Si ya existen páginas wiki de usuario, se requiere un script de migración: mover archivos en disco + actualizar strings `wiki_path` en BD.

### Wiki index (FalkorDB)

Añadir propiedad `user_id` (nullable) a nodos `WikiPage`. Las páginas de conocimiento general tienen `user_id=null`; las de usuario llevan su `user_id`. Las queries KNN de `search_wiki_knowledge` filtran por `user_id IS NULL OR user_id = $user_id` para devolver solo conocimiento relevante.

Alternativa más limpia: dos grafos separados en FalkorDB (`wiki_index` para conocimiento general, `user_wiki_index` para contenido de usuario). Evita filtros en queries y aísla operaciones de dreamer/keeper de las del sensei.

### Sesión ADK

`user_id` ya existe en las sesiones ADK (usado para routing de confirmaciones). Pasar a ser el ID de la entidad `User` en BD en lugar del `telegram_user_id` crudo.

### Punto de partida al retomar

1. Crear `User` + migration.
2. Añadir `user_id` a `Bonsai` + migration con backfill.
3. Cambiar builders de `wiki_path` al nuevo prefijo.
4. Añadir `user_id` a nodos `WikiPage` del índice (o dividir en dos grafos).
5. Actualizar context de sesión ADK para usar `User.id`.
6. Tests de aceptación con usuarios distintos y verificación de aislamiento.

**Dependencia:** Ninguna. Puede implementarse independientemente. FUTURE-014 depende de esta.

---

## FUTURE-014 — Multi-colección por usuario

**Contexto:**
Con la identidad de usuario establecida (FUTURE-013), esta iniciativa añade el concepto de `Collection` como agrupación de bonsáis dentro de un usuario. Un usuario puede tener varias colecciones (jardín, taller, vivero). El sensei trabaja en el contexto de una colección activa fijada en la sesión.

**Dependencia obligatoria:** FUTURE-013 implementado.

### Entidad `Collection`

```
Collection
  id
  user_id       FK → User
  name          str
  description   str (nullable)
  created_at

Bonsai
  collection_id    FK → Collection    ← reemplaza user_id directo
```

Alembic migrations:
1. `create_collection_table`
2. `add_collection_id_to_bonsai` — crear una colección default por usuario, backfill, luego NOT NULL, eliminar `user_id` directo de `Bonsai`.

### Contexto de colección activa en sesión

`active_collection_id` en session state de ADK — se fija cuando el usuario dice "hablemos de mi colección del jardín". Persiste hasta cambio explícito (mismo patrón que `user_location`).

### Resolución de ambigüedad

Cuando el usuario menciona un árbol sin especificar colección:
- Si el árbol existe en exactamente una colección del usuario → resuelve sin preguntar.
- Si existe en varias → `ask_selection` dentro del tool (ADR-011). El LLM no orquesta la resolución.
- Si `active_collection_id` está fijado en sesión → filtra por esa colección primero.

### Herramientas nuevas del sensei

- `switch_collection(name)` — cambia `active_collection_id` en sesión; lista colecciones si no hay coincidencia exacta.
- `list_collections()` — muestra las colecciones del usuario con conteo de árboles.
- Las herramientas de gestión de bonsáis (`create_bonsai`, `list_bonsais`, etc.) reciben `collection_id` del contexto de sesión.

### Punto de partida al retomar

1. Crear `Collection` + migration + colección default por usuario.
2. Migrar `Bonsai.user_id` → `Bonsai.collection_id`.
3. Actualizar todos los tools que reciben `user_id` para recibir también `collection_id`.
4. Añadir `switch_collection` y `list_collections` al sensei.
5. Implementar resolución de ambigüedad vía `ask_selection` en tools que buscan bonsáis por nombre.
6. Tests de aceptación con múltiples colecciones y verificación de aislamiento.
