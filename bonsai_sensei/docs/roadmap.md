# Trabajo futuro

Iniciativas pendientes que aún no están listas para implementar. Consultar antes de empezar tareas relacionadas.

---

## FUTURE-022 — Mover advisor/session_manager/runner a capa de infraestructura

**Motivación**: `advisor.py`, `session_manager.py` y `runner.py` viven en `domain/services/sensei/` pero son adaptadores de infraestructura ADK — saben de `Runner`, `InMemorySessionService`, `App`, lifecycle de sesiones. Son **port adapters** que conectan el canal de usuario (Telegram/HTTP) con los agentes del dominio, no lógica de dominio.

**Cambio propuesto**:
```
domain/services/sensei/       ← solo agentes, instrucciones, factories
infrastructure/advisor/        ← advisor.py, session_manager.py, runner.py
infrastructure/adk/            ← tool_tracer.py, tool_limiter.py,
                                  single_tool_call_callback.py
```

`tool_tracer.py` (OpenTelemetry), `tool_limiter.py` (ToolContext ADK) y `single_tool_call_callback.py` (after_model_callback ADK) viven actualmente en `domain/services/` pero son adaptadores de infraestructura ADK/observabilidad, no lógica de dominio.

**Bloqueante**: requiere actualizar imports en `main.py`, `api/advice.py`, todos los factories de agentes, y tests. Sin impacto funcional.

---

## FUTURE-021 — Rediseño del dominio con DDD

**Motivación**: El dominio actual mezcla patrones. Las entidades SQLModel son anémicas (solo datos), los "repositorios" (`cultivation_plan.py`, `bonsai_photo_store.py`, etc.) hacen CRUD directo con `@with_session`, y los "domain services" son en realidad herramientas de agente ADK. No hay aggregates, value objects ni domain events definidos explícitamente.

**Problema concreto que lo originó**: `link_recent_photos_to_work` cruza la frontera entre el aggregate `PlannedWork` y el aggregate `BonsaiPhoto`. En DDD estricto, esto es trabajo de un Domain Service, pero el proyecto no tiene esa capa separada de los agentes ADK.

**Alcance del rediseño**:
- Identificar aggregates, aggregate roots y value objects para cada bounded context (garden, cultivation, storekeeper).
- Separar repositorios DDD (solo persistencia del aggregate) de los domain services (lógica de negocio que cruza fronteras).
- Decidir si las entidades SQLModel deben ser ricas (comportamiento en el aggregate) o seguir anémicas con repositorios que encapsulan la lógica.
- Revisar si los `@with_session` stores actuales son repositorios DDD o anti-patterns.
- Documentar los bounded contexts y su mapping al código.

**No urgente**: el diseño actual funciona y los tests pasan. Abordar cuando haya tiempo para refactor profundo sin presión de features.

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

## ~~FUTURE-019~~ — Gestión de planes activos ante enfermedades y plagas ✅

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

`get_recent_unlinked_pest_events` ([bonsai_history.py](../src/bonsai_sensei/domain/bonsai_history.py)) ya existe — devuelve eventos `pest_detection` sin `phytosanitary_application` vinculada en los últimos N días. Úsalo en `_build_bonsai_snapshots` ([runner.py](../src/bonsai_sensei/domain/services/mimamori/runner.py)):

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
- `domain/services/mimamori/runner.py` — añadir detección en `_build_bonsai_snapshots`, nueva dependencia `get_recent_unlinked_pest_events_func` + `get_recently_abandoned_plans_func`
- `domain/services/mimamori/scheduler.py` — propagar nuevas dependencias
- `domain/services/mimamori/templates/reflection_context.j2` — secciones condicionales para riesgo activo y recuperación pendiente

### Punto de partida al retomar

1. Enriquecer `execute_create_pest_event` con `active_fertilization_plan` y `active_design_plan` en la respuesta.
2. Añadir `get_recently_abandoned_plans` en `bonsai_history.py`.
3. Añadir detección de riesgo y recuperación en `_build_bonsai_snapshots` de mimamori.
4. Actualizar `reflection_prompt.j2` con las dos secciones condicionales.
5. Propagar dependencias por factory y scheduler.
6. Test de aceptación: registrar plaga con plan activo → verificar respuesta enriquecida. Registrar tratamiento fitosanitario → verificar que mimamori detecta recuperación.

---

## ~~FUTURE-020~~ — Activar lectura de memoria episódica en el sensei y agentes de plan ✅

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

**Fix:** En `run_mimamori` ([runner.py](../src/bonsai_sensei/domain/services/mimamori/runner.py)), antes de renderizar el prompt, llamar a `search_memory` (HTTP) con query `"conversaciones recientes bonsáis últimos 7 días"` e incluir los hechos recuperados en `reflection_prompt.j2` como sección `{% if recent_memory_facts %}`.

**Dependencia:** `EPISODIC_MEMORY_URL` configurado y servicio corriendo. Independiente de FUTURE-017/018/019.

### Archivos afectados

- `domain/services/sensei.py` — añadir sección de memoria en `SENSEI_INSTRUCTION`
- `domain/services/cultivation/plan/manage_plan.py` — llamar a `search_memory` antes del clarification loop; propagar `episodic_memory_url` por factory
- `domain/services/cultivation/plan/fertilization/templates/clarification_agent_prompt.j2` — sección `recalled_preferences`
- `domain/services/cultivation/plan/design/templates/clarification_agent_prompt.j2` — idem
- `domain/services/mimamori/runner.py` — llamar a `search_memory`; propagar resultado al template
- `domain/services/mimamori/templates/reflection_context.j2` — sección `recent_memory_facts`

### Punto de partida al retomar

1. Verificar que `load_memory` aparece en las tools del sensei cuando `memory_service` está activo (loguear tools disponibles al arrancar).
2. Añadir sección de memoria en `SENSEI_INSTRUCTION` y probar con pregunta cross-sesión.
3. Implementar llamada HTTP a `search_memory` en `manage_plan.py` antes del clarification loop; inyectar en template como `recalled_preferences`.
4. Implementar llamada en `run_mimamori`; inyectar en template como `recent_memory_facts`.
5. Tests de integración: mock del endpoint HTTP de `episodic_memory` para verificar que se llama con las queries correctas en los tres puntos.

---

## ~~FUTURE-020~~ — Extraer boilerplate de InMemoryRunner a factory compartida ✅

**Contexto:**
El patrón `Agent → InMemoryRunner → create_session → run_async` está copiado en ~12 ficheros:
`fertilizer_recommendation_runner.py`, `phytosanitary_recommendation_runner.py`, `plan_evaluation_runner.py`,
`photo_analysis_runner.py`, `photo_comparison_runner.py`, `fertilizer_wiki_compiler.py`,
`phytosanitary_wiki_compiler.py`, `species_wiki_compiler.py`, `pest_wiki_compiler.py`,
`pest_catalog_seeder.py`, `mimamori_agent_runner.py`, y otros.

La única utilidad compartida hoy es `extract_text_from_events.py`. El loop de sesión se copia-pega entero.

### Abstracción propuesta

Factory `create_single_turn_llm_runner` en `domain/services/llm_runner.py`:

```python
def create_single_turn_llm_runner(
    model, app_name, instruction, tools=(), max_llm_calls=10
) -> Callable[[types.Content], Coroutine]:
    agent = Agent(model=model, name=app_name, instruction=instruction, tools=list(tools))
    runner = InMemoryRunner(agent=agent, app_name=app_name)

    async def run(message: types.Content):
        session_id = str(uuid.uuid4())
        await runner.session_service.create_session(
            app_name=app_name, user_id=app_name, session_id=session_id
        )
        return runner.run_async(
            user_id=app_name, session_id=session_id,
            new_message=message, run_config=RunConfig(max_llm_calls=max_llm_calls)
        )

    return run
```

Encaja con el patrón CLAUDE.md: factory como composition root, `run` como closure puro sin I/O propio.

**No aplica a:**
- `advisor.py` + `mimamori_agent_runner.py` — usan `Runner` real con `memory_service` (variante distinta)
- `clarification_runner.py` — marcado para reescritura por ADR-015

### Implementado

`domain/services/llm_runner.py` creado con `create_single_turn_llm_runner` (async generator pattern).

Migrados 7 runners: `fertilizer_recommendation_runner.py`, `phytosanitary_recommendation_runner.py`, `plan_evaluation_runner.py`, `photo_comparison_runner.py`, `photo_analysis_runner.py`, `pest_wiki_compiler.py`, `species_wiki_compiler.py`.

No migrados por per-call tool state: `fertilizer_wiki_compiler.py`, `phytosanitary_wiki_compiler.py`, `pest_catalog_seeder.py`.
No tocados por diseño: `advisor.py`, `mimamori_agent_runner.py`, `clarification_runner.py`, `manage_plan.py`, `design/manage.py`, `plan_proposal_runner.py` (Workflow runners o ADR-015).

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

## FUTURE-011 — DesignVision: visión artística evolutiva del bonsái

**Contexto:**
El agente de plan de diseño produce un calendario de trabajos técnicos, pero carece de ancla visual. El usuario necesita ver cómo evolucionará el árbol como obra artística antes de planificar. Esta iniciativa introduce `DesignVision` como entidad que captura esa visión mediante un diálogo abierto y una cadena de estados estructurados que se materializan en sketches generados por IA. El `DevelopmentPlan` se crea *a partir* de la visión, no al revés.

**Principio de diseño central:** el schema textual (`BonsaiDesignState`) es la fuente de verdad. Los sketches son visualizaciones del schema, no el sustrato del razonamiento. El LLM razona sobre schemas; Imagen API renderiza el resultado. Esto garantiza coherencia estructural, trazabilidad de decisiones y aplicación fiable de reglas de especie.

---

### Entidades

```
DesignVision
  id
  bonsai_id         FK → bonsai
  status            "active" | "archived"
  created_at
  archived_at       nullable
  wiki_path         ruta al directorio de sketches (design-plans/{periodo}/)

DesignVisionPhase
  id
  design_vision_id  FK → design_vision
  phase_order       int (0 = estado actual, 1..N = fases intermedias, -1 = visión final)
  label             str  (ej. "temporada 1", "temporada 2", "visión final")
  state_json        BonsaiDesignState  ← schema estructurado de esta fase
  sketch_path       ruta al archivo de imagen generado (nullable hasta que se renderice)

PhaseTransition
  id
  design_vision_id  FK → design_vision
  from_phase_order  int
  to_phase_order    int
  status            "pending" | "applied" | "needs_recompute"
  techniques_json   lista de Technique  ← trabajos necesarios para pasar de una fase a la siguiente
  expected_growth   GrowthEstimate      ← crecimiento natural esperado entre fases
```

Un árbol tiene como máximo una `DesignVision` con `status = "active"`. Cuando se sustituye, la anterior pasa a `archived`.

---

### BonsaiDesignState — schema por fase

Cada `DesignVisionPhase` persiste un `BonsaiDesignState` que describe el árbol en ese punto de la visión. El schema captura anatomía inmutable (tronco, ramas primarias, madera muerta) y estado mutable (follaje, espacio negativo, intención de diseño).

```json
{
  "version": "1.0",
  "phase_order": 0,
  "provenance": {
    "type": "photo_initial | photo_recalibration | planned",
    "photo_uri": "...",
    "recalibrates_phase": null
  },
  "tree_state": {
    "style_current": "moyogi",
    "trunk": {
      "base_position": "centrado, inclinación leve izquierda",
      "movement": "curva suave hacia arriba con ligero giro en el tercio superior",
      "visual_priority": "primary_feature",
      "preserve_exact_line": true,
      "visibility": "dominant"
    },
    "primary_branches": [
      {
        "id": "b1",
        "position": "primer tercio inferior izquierda",
        "direction": "se extiende izquierda y hacia delante",
        "preserve": true
      }
    ],
    "deadwood": {
      "presence": true,
      "location": "apex y rama b2 superior derecha",
      "importance": "dominant_focal_point",
      "preserve": true
    },
    "foliage_pads": [
      {
        "id": "fp1",
        "position": "inferior izquierda",
        "role": "primera rama principal",
        "size": "large",
        "shape": "horizontal extendida",
        "direction": "hacia izquierda y adelante"
      }
    ],
    "negative_space": {
      "current_level": "low"
    }
  },
  "design_intent": {
    "style_target": "moyogi refinado",
    "aesthetic_goals": ["abrir espacio negativo en apex", "definir pads triangulares"],
    "intensity": "moderate",
    "negative_space_target": "medium"
  },
  "planned_changes": {
    "preserve": ["línea exacta del tronco", "jin del apex", "rama b1"],
    "reduce": ["densidad follaje zona superior derecha"],
    "create": ["pad triangular fp3 zona media izquierda"],
    "avoid": ["eliminar más del 30% del follaje total — especie pino"]
  },
  "target_state": {
    "description": "Copa más aireada con tres pads triangulares bien definidos. Madera muerta del apex visible como elemento focal.",
    "foliage_pads": [
      {
        "id": "fp1",
        "position": "inferior izquierda",
        "role": "primera rama principal",
        "size": "large",
        "shape": "horizontal extendida",
        "direction": "hacia izquierda y adelante"
      }
    ]
  }
}
```

---

### PhaseTransition — técnicas y crecimiento esperado

Cada transición entre fases persiste las técnicas necesarias y el crecimiento natural esperado. Las técnicas se derivan de la diferencia entre `tree_state` de fase N y `target_state` de fase N, filtradas por las reglas de especie de la wiki.

```json
{
  "techniques": [
    {
      "id": "t1",
      "category": "pruning | wiring | defoliation | repotting | jin_creation | pinching | grafting",
      "description": "reducir copa derecha superior para abrir espacio negativo hacia el apex",
      "target_elements": ["fp2", "b3"],
      "species_compatible": true,
      "risk_level": "low | medium | high | lethal",
      "timing_constraint": "post-dormancy | growing_season | any",
      "becomes_work_item": true
    }
  ],
  "expected_growth": {
    "seasons_estimated": 2,
    "foliage_density_change": "increase_moderate",
    "branch_extension": "ramas primarias extienden ~8cm",
    "notes": "pino: no recupera follaje eliminado — conservar mínimo 1 par de acículas por rama"
  }
}
```

El campo `becomes_work_item: true` marca las técnicas que se convierten directamente en `PlannedWork` del `DevelopmentPlan`. Las reglas de especie (`risk_level: "lethal"`) provienen de la wiki y se aplican durante el razonamiento textual, no durante la generación de imagen.

---

### Flujo de generación (razonamiento textual → sketch como output)

El razonamiento ocurre sobre schemas; la imagen es el resultado final, no el input del siguiente paso.

**Fase 0 — extracción inicial (único paso visual→textual):**
1. Foto real más reciente → LLM visión → `BonsaiDesignState_0` (provenance: `photo_initial`)
2. Usuario valida y corrige el schema antes de continuar

**Fases 1..N — razonamiento textual:**
1. `BonsaiDesignState_N` + `design_intent` + wiki de especie → LLM texto → `PhaseTransition_N→N+1` + `BonsaiDesignState_N+1`
2. Usuario revisa técnicas y estado objetivo; puede ajustar antes de renderizar
3. `BonsaiDesignState_N+1` → prompt estructurado → Imagen API → `Sketch_N+1`

Los sketches no se encadenan entre sí. Cada sketch se genera desde el schema de su fase — el schema es la continuidad, no la imagen.

---

### Recalibración — nueva foto en cualquier fase

En cualquier momento el usuario puede aportar una nueva foto del árbol real. Esto actualiza el estado observado y puede invalidar transiciones planificadas.

1. Nueva foto → LLM visión → `BonsaiDesignState_N_observed` (provenance: `photo_recalibration`, `recalibrates_phase: N`)
2. LLM texto: `delta(State_N_planned, State_N_observed)` → lista de diferencias
3. Usuario revisa delta: acepta o ajusta
4. `BonsaiDesignState_N_observed` reemplaza `State_N_planned` como base
5. Transiciones `N→N+1`, `N+1→N+2`... pasan a `status: "needs_recompute"`
6. LLM recomputa cada transición afectada desde el nuevo estado observado
7. Sketches de fases downstream se invalidan y regeneran desde los nuevos schemas

El árbol real manda; el plan se adapta.

---

### Creación del DevelopmentPlan desde la visión

Una vez creada la `DesignVision`, el `DevelopmentPlan` se genera leyendo la `PhaseTransition` cuyo `from_phase_order` corresponde a la fase actual:

1. Filtrar técnicas donde `becomes_work_item: true`
2. Agrupar por `timing_constraint` → calendario de temporada
3. Usar `expected_growth.seasons_estimated` para proyectar fechas

El plan no infiere técnicas desde imágenes — las lee de la transición ya validada.

---

### Relación con el plan de fertilización

El `DevelopmentPlan` generado incluye los trabajos técnicos. El plan de fertilización se crea por separado a partir de ese plan, de forma explícita por el usuario, respetando ADR-011 (sin encadenamiento implícito).

---

### Wiki structure

```
users/{user_id}/bonsai/{slug}/design-plans/{periodo}/
  design-plan.md          ← wiki del DevelopmentPlan (existente)
  sketches/
    00-estado-actual.png
    01-temporada-1.png
    02-temporada-2.png
    final.png
  states/
    00-estado-actual.json   ← BonsaiDesignState por fase
    01-temporada-1.json
    02-temporada-2.json
    final.json
```

---

### Prompts

Los prompts de generación están versionados en [`docs/image_prompts.md`](image_prompts.md):
- `sketch-from-photo-v2` (activo) — foto real → `BonsaiDesignState_0` inicial.
- Pendiente: prompt schema→sketch (renderizado de `BonsaiDesignState` → sketch de tinta). Las constraints `preserve: true` del schema se inyectan como restricciones duras.

---

**Dependencia:** FUTURE-012 implementado ✅.

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
