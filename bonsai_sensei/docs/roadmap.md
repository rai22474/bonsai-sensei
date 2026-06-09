# Trabajo futuro

Iniciativas pendientes que aún no están listas para implementar. Consultar antes de empezar tareas relacionadas.

---

## FUTURE-016 — Refinación de trabajos planificados

**Contexto:**
Algunos trabajos planificados requieren una sesión de análisis previo a su ejecución. Ejemplos: estudio de madera muerta en un pino (fotos desde múltiples ángulos para decidir dónde y cómo trabajarla), mekiri (el asistente ayuda a decidir qué brotes cortar). El sistema actual no tiene mecanismo para anclar una sesión conversacional diagnóstica a un `PlannedWork` concreto ni para persistir su resultado.

**Dependencia:** FUTURE-012 (`DevelopmentPlan`) implementado ✅.

### Entidad `WorkRefinement`

```
WorkRefinement
  id
  planned_work_id   FK → planned_work  (CASCADE on delete)
  user_id           str
  status            str  ("in_progress" | "completed" | "abandoned")
  wiki_path         str  (users/{user_id}/bonsai/{slug}/refinements/{work_id}-{date}.md)
  created_at
  completed_at
```

### Flujo conversacional

El `refinement_advisor` es un agente libre en `InMemoryRunner` efímero (evita acumulación de eventos en la sesión principal). Recibe el `PlannedWork` como contexto inicial y opera con:

- Tool de lectura de wiki del trabajo planificado y del plan de desarrollo asociado
- Tool de análisis de foto (`analyze_photo`) — multimodal, resultados acumulados en estado de sesión
- `RequestInput` (patrón ADR-015, `rerun_on_resume=True`) para el loop multi-turno: pedir foto → analizar → pedir otra foto o hacer preguntas → siguiente turno
- `finalize_refinement` — tool determinístico (patrón ADR-009): ensambla todo el contexto (fotos analizadas + diálogo + wiki de especie + plan) → LLM runner genera contenido wiki → escribe página → actualiza `WorkRefinement.status = "completed"`. Garantiza la escritura.

El outer sensei delega al `refinement_advisor` vía tool call y recibe resultado cuando termina. La sesión del `refinement_advisor` nunca escala al outer agent — la compaction (ADR-004/ventana deslizante) ya cubre conversaciones largas, pero la separación en `InMemoryRunner` propio sigue siendo el diseño correcto por aislamiento de estado.

### Output

Wiki page en `users/{user_id}/bonsai/{slug}/refinements/{work_id}-{date}.md`. La página del `PlannedWork` puede linkear a ella. FalkorDB la indexa automáticamente vía el hook existente en `write_wiki_page` — `search_wiki_knowledge` la encontrará en conversaciones futuras sin acoplamiento adicional.

### Archivos nuevos

- `domain/work_refinement.py` — entidad SQLModel
- `domain/work_refinement_store.py` — CRUD
- `alembic/versions/*_add_work_refinement.py`
- `api/work_refinements.py` — REST CRUD para cleanup en tests de aceptación
- `services/cultivation/refinement/` — agente + tools + templates

### Punto de partida al retomar

1. Crear `WorkRefinement` + store + migración.
2. Crear `api/work_refinements.py` con DELETE para cleanup de tests.
3. Implementar `finalize_refinement` tool (ADR-009 pattern) con su template Jinja2.
4. Implementar el `refinement_advisor` como agente libre con `RequestInput` HITL.
5. Wiring en `factory.py` y `main.py`.
6. Tests de aceptación BDD (escenario: usuario sube foto → asistente analiza → usuario confirma → wiki escrita).

---

## FUTURE-017 — Plan de diseño como entrada del plan de fertilización ✅

**Contexto:**
El plan de fertilización se genera sin conocer el plan de diseño activo del bonsái. Sin embargo, los objetivos de fertilización dependen directamente de la fase de desarrollo: engrosamiento de tronco → nitrógeno alto durante la temporada; refinamiento de ramaje → equilibrio NPK o reducción de N; reposo forzado → fertilización mínima o nula. El agente de fertilización actualmente pregunta el objetivo al usuario desde cero, sin aprovechar la información ya definida en el plan de diseño.

**Objetivo:** inyectar el contenido del plan de diseño activo en el contexto de fertilización para que el agente pueda proponer objetivos coherentes y el usuario solo necesite confirmar o ajustar, en lugar de repetir lo que ya está planificado.

**Diseño:**

1. `load_bonsai_plan_context` ([plan_context.py](../src/bonsai_sensei/domain/services/cultivation/plan/plan_context.py)) debe leer el wiki del plan de diseño activo (`users/{user_id}/bonsai/{slug}/design-plans/`) y añadirlo al dict de contexto como `active_design_plan_content`.

2. `create_manage_fertilization_plan_tool` ([manage.py](../src/bonsai_sensei/domain/services/cultivation/plan/fertilization/manage.py)) debe pasar `get_active_development_plan_func` a `create_manage_plan_tool` como dependencia inyectada, o leer el wiki directamente vía `list_wiki_files_func` + `read_wiki_page_func`.

3. Los templates `clarification_agent_prompt.j2` y `plan_proposal_prompt.j2` deben incluir una sección condicional con el plan de diseño activo, indicando al LLM que lo use como punto de partida para proponer objetivos.

**Comportamiento esperado:**
- Si existe plan de diseño activo → el agente de clarificación lo presenta al usuario como contexto y sugiere objetivos alineados con la fase de diseño. El usuario puede confirmar, ajustar o ignorar.
- Si no existe plan de diseño → el flujo actual se mantiene sin cambios.

**Dependencia:** FUTURE-012 (`DevelopmentPlan`) implementado ✅.

### Punto de partida al retomar

1. Añadir `active_design_plan_content` en `load_bonsai_plan_context`: buscar el wiki más reciente en `users/{user_id}/bonsai/{slug}/design-plans/` (excluir `index.md`).
2. Propagar el valor por `bonsai_context` hasta los templates de fertilización.
3. Actualizar `clarification_agent_prompt.j2`: añadir sección condicional `{% if active_design_plan_content %}` que muestre el plan y guíe al agente a usarlo como base para preguntar el objetivo.
4. Actualizar `plan_proposal_prompt.j2`: incluir el plan de diseño en la sección de contexto para que la propuesta de fertilizantes sea coherente con la fase.
5. Test de aceptación: bonsái con plan de diseño activo → crear plan de fertilización → verificar que el objetivo propuesto refleja la fase de diseño.

---

## FUTURE-018 — Mimamori detecta plan de fertilización desalineado con el diseño ✅

**Contexto:**
Es posible tener un plan de fertilización activo creado bajo un objetivo de diseño anterior, y luego reemplazar el plan de diseño (nueva fase, nuevo objetivo) sin recordar ajustar la fertilización. Mimamori debe detectar este desalineamiento y alertar al cultivador en su reflexión matinal.

**Detección determinista:**
Ambas entidades tienen `created_at`. Cuando un plan de diseño se reemplaza, se abandona el anterior y se crea uno nuevo — el `created_at` del nuevo `DevelopmentPlan` supera al `created_at` del `FertilizationPlan` activo. Esto es condición necesaria y suficiente para detectar el desalineamiento. No se requiere campo nuevo ni migración.

```
dev_plan.created_at > fert_plan.created_at
→ diseño actualizado después de crear la fertilización
→ fertilización potencialmente desalineada
```

**Diseño:**

1. `run_mimamori` ([runner.py](../src/bonsai_sensei/domain/services/cultivation/mimamori/runner.py)) recibe `get_active_fertilization_plan_func` como nueva dependencia inyectada (mismo patrón que `get_active_development_plan_func`).

2. `_build_bonsai_snapshots` computa el flag por bonsái:
   ```python
   fert_plan = get_active_fertilization_plan_func(bonsai_id=bonsai.id)
   fertilization_outdated = (
       dev_plan is not None
       and fert_plan is not None
       and dev_plan.created_at > fert_plan.created_at
   )
   ```
   El snapshot añade `fertilization_outdated: bool` y, si aplica, `fertilization_plan_goal: str` (el goal con el que se creó el plan) y `current_design_goal: str`.

3. `reflection_prompt.j2` añade una sección condicional al inicio:
   ```
   {% set outdated = bonsais | selectattr("fertilization_outdated") | list %}
   {% if outdated %}
   ## ⚠️ Planes de fertilización desalineados
   {% for b in outdated %}
   - **{{ b.name }}**: el plan de diseño se actualizó (objetivo actual: {{ b.current_design_goal }}) después de crear el plan de fertilización (objetivo original: {{ b.fertilization_plan_goal }}).
   {% endfor %}
   {% endif %}
   ```
   Mimamori recibe los datos; su LLM redacta el aviso con tono de maestro.

4. Propagar `get_active_fertilization_plan_func` en `scheduler.py` (`_dispatch_mimamori` + `create_mimamori_scheduler`) y en el factory que construye mimamori.

**Dependencia:** FUTURE-012 (`DevelopmentPlan`) implementado ✅. Compatible con FUTURE-017 (pueden implementarse en cualquier orden).

### Punto de partida al retomar

1. Añadir `get_active_fertilization_plan_func` a la firma de `run_mimamori` y a `_dispatch_mimamori` / `create_mimamori_scheduler`.
2. Añadir cálculo de `fertilization_outdated` en `_build_bonsai_snapshots`.
3. Actualizar `reflection_prompt.j2` con la sección de desalineamientos.
4. Propagar la nueva dependencia en el factory que instancia mimamori.
5. Test de aceptación: crear plan de fertilización → crear nuevo plan de diseño → ejecutar mimamori → verificar que el mensaje menciona el desalineamiento.

---

## FUTURE-019 — Gestión de planes activos ante enfermedades y plagas

**Contexto:**
Cuando se detecta una enfermedad o plaga en un bonsái que tiene planes activos de fertilización y/o diseño, los planes pueden quedar desalineados con la realidad: un árbol enfermo no debe recibir fertilización intensa, y los trabajos de diseño (poda, alambrado) pueden agravar el estrés. Actualmente el sistema no tiene ningún mecanismo para alertar ni gestionar este escenario.

**Decisión de diseño — sin status "paused":**
Añadir un estado intermedio `paused` no aporta valor real. Si un plan de fertilización junio-septiembre se pausa en julio por enfermedad y el árbol se recupera en agosto, las fechas de junio ya son pasado — el plan necesita recrearse de todas formas. La estrategia correcta es **abandon + recrear con nuevo contexto**, mismo patrón ya establecido. El `abandonment_reason` captura el motivo (`"disease_pause: <nombre_plaga>"`).

### Componente 1 — `create_pest_event` enriquece la respuesta

`execute_create_pest_event` ([create_pest_event.py](../src/bonsai_sensei/domain/services/garden/caretaker/create_pest_event.py)) ya acepta `get_active_phytosanitary_plan_func`. Añadir dos dependencias más: `get_active_fertilization_plan_func` y `get_active_development_plan_func`.

Respuesta enriquecida:
```python
{
  "status": "success",
  "pest_event_id": ...,
  "active_phytosanitary_plan": bool,
  "active_fertilization_plan": bool,   # nuevo
  "active_design_plan": bool,          # nuevo
}
```

El LLM (caretaker → sensei) recibe este contexto y puede proactivamente ofrecer abandonar los planes afectados y explicar por qué.

### Componente 2 — Mimamori detecta desalineamiento activo

`get_recent_unlinked_pest_events` ([bonsai_history.py](../src/bonsai_sensei/domain/bonsai_history.py)) ya existe — devuelve eventos `pest_detection` sin `phytosanitary_application` vinculada en los últimos N días. Úsalo en `_build_bonsai_snapshots` ([runner.py](../src/bonsai_sensei/domain/services/cultivation/mimamori/runner.py)):

```python
unlinked_pests = get_recent_unlinked_pest_events_func(bonsai_id=bonsai.id, hours=720)
snapshot["unlinked_pest_names"] = [e.payload.get("pest_name") for e in unlinked_pests]
snapshot["fertilization_at_risk"] = bool(unlinked_pests) and fert_plan is not None
snapshot["design_at_risk"] = bool(unlinked_pests) and dev_plan is not None
```

`reflection_prompt.j2` recibe estos flags y mimamori redacta el aviso con tono de maestro.

### Componente 3 — Mimamori detecta recuperación (planes para recrear)

Cuando el árbol se recupera (plaga resuelta = no hay `unlinked_pest_events` recientes) pero hay planes abandonados con `abandonment_reason` que contiene `"disease_pause"` en los últimos 90 días → mimamori sugiere recrear los planes.

Requiere nueva función en store: `get_recently_abandoned_plans(bonsai_id, days=90, reason_contains="disease_pause")`.
Snapshot añade `plans_pending_recreation: list[str]` (nombres de los tipos de plan: fertilization, design).

**Dependencia:** FUTURE-012 (`DevelopmentPlan`) implementado ✅. Compatible con FUTURE-017 y FUTURE-018 (implementar en cualquier orden).

### Archivos afectados

- `domain/services/garden/caretaker/create_pest_event.py` — añadir 2 dependencias + enriquecer respuesta
- `domain/services/garden/caretaker/factory.py` — propagar nuevas dependencias
- `domain/bonsai_history.py` — añadir `get_recently_abandoned_plans`
- `domain/services/cultivation/mimamori/runner.py` — añadir detección en `_build_bonsai_snapshots`, nueva dependencia `get_recent_unlinked_pest_events_func` + `get_recently_abandoned_plans_func`
- `domain/services/cultivation/mimamori/scheduler.py` — propagar nuevas dependencias
- `domain/services/cultivation/mimamori/templates/reflection_prompt.j2` — secciones condicionales para riesgo activo y recuperación pendiente

### Punto de partida al retomar

1. Enriquecer `execute_create_pest_event` con `active_fertilization_plan` y `active_design_plan` en la respuesta.
2. Añadir `get_recently_abandoned_plans` en `bonsai_history.py`.
3. Añadir detección de riesgo y recuperación en `_build_bonsai_snapshots` de mimamori.
4. Actualizar `reflection_prompt.j2` con las dos secciones condicionales.
5. Propagar dependencias por factory y scheduler.
6. Test de aceptación: registrar plaga con plan activo → verificar respuesta enriquecida. Registrar tratamiento fitosanitario → verificar que mimamori detecta recuperación.

---

## FUTURE-020 — Activar lectura de memoria episódica en el sensei y agentes de plan

**Contexto:**
La memoria episódica está **escribiendo** correctamente: tras cada turno de conversación, `_capture_session_to_memory` llama a `EpisodicMemoryService.add_session_to_memory` ([advisor.py](../src/bonsai_sensei/domain/services/advisor.py)), que indexa los mensajes en Graphiti. Pero la **lectura nunca ocurre**:

- ADK inyecta un tool `load_memory` automáticamente cuando el `Runner` recibe `memory_service`.
- `SENSEI_INSTRUCTION` ([sensei.py](../src/bonsai_sensei/domain/services/sensei.py)) no menciona `load_memory` → el sensei no sabe que existe ni cuándo usarlo.
- Los agentes de clarificación de planes y mimamori tampoco tienen acceso a ella.

**Objetivo:** Activar la lectura en los tres puntos donde aporta valor real.

### Punto 1 — Sensei: preguntas cross-sesión (mayor valor)

Preguntas como "¿qué le hice al Naruto el mes pasado?", "¿he notado algún problema con el Eren este año?", "¿cuándo fue la última vez que hablamos de alambrar?" no pueden responderse con la wiki ni con los eventos estructurados — necesitan el historial conversacional.

**Fix:** Añadir a `SENSEI_INSTRUCTION` una sección que indique al sensei que cuando el usuario pregunte por conversaciones anteriores, historial reciente o preferencias expresadas anteriormente, debe llamar a `load_memory` con una query semántica relevante antes de responder.

```
# Memoria episódica
Cuando el usuario pregunte por conversaciones anteriores, historial reciente o algo que "dijiste" o "hablamos", usa load_memory con una query semántica antes de responder.
```

### Punto 2 — Agentes de clarificación: preferencias persistidas

Durante la clarificación de planes (fertilización, diseño), el agente pregunta objetivos y preferencias desde cero cada vez. Si el usuario ya expresó preferencias en conversaciones pasadas ("prefiero fertilizantes orgánicos", "quiero un estilo informal upright"), recuperar esa información evita preguntas repetidas.

**Problema:** Los agentes de clarificación corren en `InMemoryRunner` efímero (no tienen acceso a `memory_service`). Alternativa: antes de lanzar el clarification loop, el tool orquestador puede llamar a `search_memory` directamente (vía HTTP a `EPISODIC_MEMORY_URL`) con una query como `"preferencias fertilización {bonsai_name}"` e inyectar el resultado en el template `clarification_agent_prompt.j2` como `{% if recalled_preferences %}` (análogo a `{% if bonsai_wiki_content %}`).

### Punto 3 — Mimamori: continuidad entre días

Mimamori genera reflexiones independientes cada día. Si el usuario mencionó ayer que observó hojas amarillas o que iba a hacer un trasplante el fin de semana, mimamori no lo sabe.

**Fix:** En `run_mimamori` ([runner.py](../src/bonsai_sensei/domain/services/cultivation/mimamori/runner.py)), antes de renderizar el prompt, llamar a `search_memory` (HTTP) con query `"conversaciones recientes bonsáis últimos 7 días"` e incluir los hechos recuperados en `reflection_prompt.j2` como sección `{% if recent_memory_facts %}`.

**Dependencia:** `EPISODIC_MEMORY_URL` configurado y servicio corriendo. Independiente de FUTURE-017/018/019.

### Archivos afectados

- `domain/services/sensei.py` — añadir sección de memoria en `SENSEI_INSTRUCTION`
- `domain/services/cultivation/plan/manage_plan.py` — llamar a `search_memory` antes del clarification loop; propagar `episodic_memory_url` por factory
- `domain/services/cultivation/plan/fertilization/templates/clarification_agent_prompt.j2` — sección `recalled_preferences`
- `domain/services/cultivation/plan/design/templates/clarification_agent_prompt.j2` — idem
- `domain/services/cultivation/mimamori/runner.py` — llamar a `search_memory`; propagar resultado al template
- `domain/services/cultivation/mimamori/templates/reflection_prompt.j2` — sección `recent_memory_facts`

### Punto de partida al retomar

1. Verificar que `load_memory` aparece en las tools del sensei cuando `memory_service` está activo (loguear tools disponibles al arrancar).
2. Añadir sección de memoria en `SENSEI_INSTRUCTION` y probar con pregunta cross-sesión.
3. Implementar llamada HTTP a `search_memory` en `manage_plan.py` antes del clarification loop; inyectar en template como `recalled_preferences`.
4. Implementar llamada en `run_mimamori`; inyectar en template como `recent_memory_facts`.
5. Tests de integración: mock del endpoint HTTP de `episodic_memory` para verificar que se llama con las queries correctas en los tres puntos.

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
El agente de plan de diseño produce un texto con técnicas y ventanas temporales. Para objetivos visuales ("afinar ápice", "dar movimiento al primer tramo") una imagen de referencia aporta información que el texto no puede transmitir. El usuario necesita ver, no solo leer.

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

**Prompts:** Los prompts de generación están versionados en [`docs/image_prompts.md`](image_prompts.md). `sketch-from-photo-v1` es el prompt inicial para Opción A — transforma una foto del árbol en un sketch de tinta en blanco y negro al estilo de un boceto de diseño tradicional.

**Dependencia:** FUTURE-012 implementado ✅ (el agente de plan de diseño es el host natural de este tool).

---

## FUTURE-014 — Multi-colección por usuario

**Contexto:**
Con la identidad de usuario establecida (FUTURE-013 implementado ✅), esta iniciativa añade el concepto de `Collection` como agrupación de bonsáis dentro de un usuario. Un usuario puede tener varias colecciones (jardín, taller, vivero). El sensei trabaja en el contexto de una colección activa fijada en la sesión.

### Entidad `Collection`

```
Collection
  id
  user_id       FK → user_settings
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
