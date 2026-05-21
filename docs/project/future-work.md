# Trabajo futuro

Iniciativas pendientes que aún no están listas para implementar. Consultar antes de empezar tareas relacionadas.

---

## FUTURE-001 — Base de conocimiento: revisión humana y calidad de la wiki

**Contexto:**
El módulo `knowledge_base/` (pipeline de ingesta + keeper) está operativo: ingesta transcripciones de YouTube, extrae tarjetas de conocimiento y el keeper mantiene la wiki a partir de esas tarjetas. Sin embargo, faltan varias capas antes de que pueda considerarse listo para producción.

### Calidad de las páginas generadas
El keeper usa actualmente un modelo ligero (`gemini-flash-lite`) y produce páginas demasiado escasas. Antes de invertir en un flujo de revisión, hay que resolver primero el problema de calidad. Opciones a evaluar:
- Cambiar el keeper a un modelo más potente (`flash` o `pro`)
- Aumentar `_MAX_LLM_CALLS` en el runner
- Bucle crítico/autocrítica: generar → evaluar → refinar → escribir

### Flujo de revisión humana
El keeper escribe páginas de forma autónoma. Es deseable un paso de revisión por un administrador antes de que los cambios sean visibles para los agentes Sensei. Conclusiones de las discusiones de diseño:
- **Mecanismo de borradores**: el keeper escribe en `wiki/drafts/` o en una rama `drafts`; los agentes Sensei leen solo desde el estado aprobado.
- **Git como control de versiones**: inicializar `wiki/` como repositorio git local; el keeper hace commit tras cada ejecución; ofrece historial y rollback sin coste adicional.
- **La UX de revisión es el problema sin resolver**: sin un remoto (GitHub/Gitea), el administrador no tiene una forma cómoda de ver cambios sin acceso SSH. Opciones evaluadas:
  - Flujo de PR en GitHub: UX de diff limpia pero alta complejidad operativa (credenciales en el servidor, webhooks, gestión de PRs).
  - Git local + pull por SSH: más simple pero sigue requiriendo acceso al servidor para revisar.
  - Endpoint REST que devuelve el diff: funcional pero mala UX para markdown.
  - Notificación por Telegram + aprobación por defecto con endpoint de rollback: la opción más pragmática por ahora.
- **Punto de partida recomendado al retomar**: implementar git local para la wiki (historial + rollback) y aprobación por defecto. Añadir un endpoint `POST /api/wiki/revert` para deshacer el último commit del keeper. Posponer la puerta de borradores/aprobación hasta que la UX de revisión esté resuelta.

### Descubrimiento de páginas del keeper
Los agentes Sensei descubren páginas wiki a través del `wiki_path` almacenado en la base de datos. Las páginas creadas por el keeper no están registradas en la base de datos, por lo que los agentes no pueden encontrarlas. Este problema se resuelve con el índice de navegación descrito en FUTURE-002 — no requiere infraestructura adicional.

### Orden de trabajo al retomar
1. Mejorar la calidad de salida del keeper (modelo + llamadas, o bucle crítico)
2. Git local para la wiki (historial + rollback)
3. Aprobación por defecto + endpoint de revert
4. Índice de navegación (FUTURE-002) — permite a los agentes encontrar páginas del keeper
5. Revisitar la UX de revisión una vez lo anterior esté estable

---

## FUTURE-002 — Índice de navegación de la wiki con embeddings

**Contexto:**
Los constructores de contexto cargan páginas wiki siguiendo enlaces conocidos registrados en la base de datos. Dos problemas a medida que la wiki crece:
1. Las páginas creadas por el keeper no están en la base de datos — los agentes no las encuentran.
2. Cargar todas las páginas enlazadas añade ruido y coste en tokens — no todas son relevantes para la petición actual.

**Solución: grafo de metadatos paralelo a la wiki.**
El keeper mantiene una estructura `wiki-index/` que espeja `wiki/` con un fichero JSON por página:

```
wiki/                          wiki-index/
  bonsai/                        bonsai/
    goku/                          goku/
      index.md          →            index.json
      reports/                       reports/
        2026-04-10-health.md →         2026-04-10-health.json
```

Cada `page.json` contiene:
```json
{
  "abstract": "Ficus retusa. Análisis de salud de abril 2026. Clorosis leve en ápice.",
  "updated": "2026-04-10",
  "links": ["bonsai/goku/index.md"],
  "embedding": [0.12, -0.34, 0.08, "..."]
}
```

**Responsabilidad del keeper:**
Cada vez que escribe una página, genera el abstract + embedding y escribe/actualiza su `page.json` en `wiki-index/`. La actualización es local al nodo — sin fichero global que gestionar.

**Navegación por los agentes (traversal con poda):**
1. Empezar en raíces conocidas (nombres de bonsáis desde la base de datos).
2. Cargar `index.json` → calcular similitud coseno entre su embedding y el embedding del intent del usuario.
3. Seguir solo los links con similitud por encima del umbral.
4. Parar en profundidad N o cuando la similitud cae.
5. Cargar los `.md` completos solo de las páginas seleccionadas.

**Por qué JSON y no pgvector:**
Para el volumen esperado (<500 páginas), la similitud coseno sobre arrays en memoria con numpy es suficiente — microsegundos por búsqueda. pgvector añade infraestructura sin beneficio real a esta escala.

**Notas de implementación:**
- Modelo de embedding: `text-embedding-004` (Google, ya es dependencia).
- `wiki-index/` puede ir en `.gitignore` si se trata como caché regenerable, o versionarse para historial de embeddings.
- La firma de los constructores de contexto necesita recibir el intent del usuario para puntuar — cambio que afecta a todos los callers de `load_bonsai_plan_context`.
- Implementar después de FUTURE-001 §Calidad — no tiene sentido indexar páginas de baja calidad.

---

## FUTURE-003 — Taxonomía de conocimiento general y enlaces en el keeper

**Contexto:**
El keeper ingesta transcripciones y crea páginas wiki de conocimiento general (especies, técnicas, enfermedades, abonado). Sin una taxonomía definida y sin instrucciones de enlazado, el keeper produce páginas huérfanas o duplicadas que el grafo de FUTURE-002 no puede alcanzar desde los bonsáis.

**Dependencia:** FUTURE-002 (el grafo solo es útil si los enlaces existen).

### Taxonomía de la wiki

Estructura fija de secciones para conocimiento general fuera de `bonsai/`:

```
wiki/
  bonsai/               ← conocimiento de instancia (ya existe)
  species/              ← una página por especie
    ficus-retusa.md
    juniperus-chinensis.md
  techniques/           ← agrupado por disciplina
    wiring/
    pruning/
    repotting/
  fertilization/        ← protocolos por estación o tipo
    spring-protocol.md
    nitrogen-ratios.md
  diseases/             ← una página por patología
    chlorosis.md
    root-rot.md
    spider-mites.md
```

Reglas:
- Una página por concepto — sin páginas paraguas que mezclen temas.
- Nombres en minúsculas con guiones (consistente con el slug de bonsáis).
- Las páginas de instancia (`bonsai/`) enlazan a las de conocimiento general; las de conocimiento general no enlazan a instancias específicas.

### Instrucciones de enlazado para el keeper

El keeper debe crear enlaces activamente al escribir o actualizar páginas:

- **Página de especie** → enlaza a: enfermedades frecuentes, técnicas aplicables, protocolos de abonado recomendados.
- **Página de bonsái** (`bonsai/<slug>/index.md`) → enlaza a su página de especie.
- **Página de enfermedad** → enlaza a: técnicas de tratamiento, condiciones que la favorecen.
- **Página de técnica** → enlaza a: especies en las que es especialmente relevante, enfermedades que previene o trata.

Sin estas instrucciones explícitas en el prompt del keeper, el grafo de FUTURE-002 queda desconectado del conocimiento general.

### Profundidad de traversal

Los constructores de contexto deben calibrar la profundidad según el tipo de nodo:

| Profundidad | Tipo de nodo |
|-------------|-------------|
| 0 | Bonsái (raíz) |
| 1 | Especie, informes recientes, plan activo |
| 2 | Técnicas y enfermedades enlazadas desde la especie |
| 3 | Subpáginas de técnicas o tratamientos específicos |

Más allá de profundidad 3 el filtro de similitud coseno debe ser muy estricto para evitar cargar conocimiento irrelevante.

### Orden de trabajo al retomar
1. Definir y documentar la taxonomía (este fichero es suficiente como spec)
2. Actualizar el prompt del keeper con las reglas de enlazado
3. Re-ingestar transcripciones existentes con el keeper actualizado para poblar la taxonomía
4. Validar traversal desde un bonsái real hasta conocimiento general relevante

---

## FUTURE-004 — Eventos de plaga por bonsái (COMPLETADO 2026-05-21)

**Contexto:**
El sistema registra tratamientos fitosanitarios (`apply_phytosanitary`) y planes fitosanitarios, pero no tiene forma de registrar una observación de plaga como evento independiente. Sin este registro no hay trazabilidad infección → tratamiento, ni historial de plagas por bonsái para informar futuras recomendaciones.

**Estado (2026-05-21):** COMPLETADO. Catálogo `Pest`, flujo de detección, integración Tavily (FUTURE-004b), y enlace a `apply_phytosanitary` implementados. `apply_phytosanitary` detecta automáticamente eventos de plaga recientes sin tratamiento vinculado y presenta selección al usuario. Tests de aceptación verdes.

### Nuevas entidades

**`Pest`** — catálogo de plagas por especie:
- Generado automáticamente al dar de alta una especie (paso LLM separado, re-ejecutable)
- Campos: id, name, species_id (FK), wiki_path
- Misma forma que `Phytosanitary` (catálogo de productos); cada plaga tiene su ficha en la wiki

**`PestEvent`** — observación de plaga en un bonsái:
- Campos: id, bonsai_id (FK), pest_id (FK), detected_at
- Tratamiento: `PhytosanitaryApplication` existente, con un campo `pest_event_id` (FK nullable) añadido
- El tratamiento es opcional en el momento del alta del evento (puede detectarse sin tratar aún)

### Flujo conversacional

1. Usuario reporta plaga en "Hanako" → agente filtra `Pest` por la especie de Hanako → usuario selecciona
2. Se crea `PestEvent` con la plaga seleccionada
3. Agente pregunta si se ha aplicado tratamiento → si sí, flujo `apply_phytosanitary` habitual con `pest_event_id` enlazado
4. Si hay plan fitosanitario activo → agente propone revisión del plan con confirmación (no automática)

### Decisiones de diseño

- El catálogo de plagas vive en la wiki igual que los productos fitosanitarios: una página por plaga generada por LLM al crear la especie.
- Reutilizar `apply_phytosanitary` en lugar de crear un mecanismo nuevo: añadir `pest_event_id` nullable a `PhytosanitaryApplication` preserva la trazabilidad sin romper el flujo existente.
- La modificación del plan es siempre una propuesta con confirmación — nunca automática.

### Orden de trabajo al implementar

1. ~~Migración: tabla `pest`, añadir `pest_event_id` a `phytosanitary_application`~~ (done)
2. ~~Store functions + REST endpoints para `Pest` y `PestEvent`~~ (done)
3. ~~Generación de catálogo de plagas al alta de especie (LLM + wiki, re-ejecutable)~~ (done)
4. ~~Herramienta de agente: alta de `PestEvent` con confirmación~~ (done)
5. ~~Enlace a `apply_phytosanitary` desde el evento~~ (done 2026-05-21 — selección de evento reciente sin vincular)
6. ~~Propuesta de revisión de plan si hay uno activo~~ — reemplazado por aviso pasivo: `create_pest_event` devuelve `active_plan: bool`; caretaker lo menciona en texto sin preguntar. Ver ADR-011 para el razonamiento.
7. ~~Tests de aceptación~~ (done)

---

## FUTURE-004b — Búsqueda fitosanitaria online (COMPLETADO 2026-05-18)

Kikaru puede buscar productos fitosanitarios online vía Tavily cuando: (a) el catálogo no tiene productos (`no_products_available`) o (b) el usuario pide explícitamente alternativas en internet. La herramienta `search_phytosanitary_online` está implementada, wired a través de toda la cadena de fábricas, con test de aceptación verde. La recomendación puntual (`recommend_phytosanitary`) sigue siendo el camino principal cuando hay productos en catálogo.

---

## FUTURE-005 — Mejoras de orquestación entre agentes (COMPLETADO 2026-05-14)

**Contexto:**
Varias debilidades en el protocolo mitori → shokunin → sub-agente producían pérdida de información, pasos de pre-validación redundantes y comportamiento no determinista en Kikaru. Las siguientes mejoras se implementaron en una sola sesión.

### Schema de plan estructurado (Option A)

`mitori_instruction.j2` actualizado: los pasos del plan ahora incluyen un campo `parameters` (dict) junto al campo `request` en texto natural. Shokunin pasa ambos a los sub-agentes. Esto resuelve la pérdida de información donde los sub-agentes (caretaker, nursery, etc.) solo recibían una cadena `request` vaga sin los valores específicos del mensaje original del usuario.

La decisión de adoptar Option A y diferir Option C está registrada en ADR-010 (`docs/architecture/decisions.md`).

### Corrección de routing nursery + botanist

Descripciones de agentes actualizadas para que mitori no genere un paso botanist de pre-validación antes de crear un bonsái. La descripción de nursery ahora indica que la validación de especie es interna; la descripción de botanist indica que no debe invocarse como pre-paso antes de la creación de bonsái.

### Determinismo en Kikaru (selección de tipo de abonado)

`KIKARU_INSTRUCTION` actualizado: regla explícita de que una fecha concreta siempre implica abonado puntual (nunca llamar a `clarify_fertilization_type`). Tras recibir "puntual" de `clarify_fertilization_type`, llamar inmediatamente a `create_fertilizer_application`.

### Descripción de botanist ampliada

La descripción del agente botanist se actualizó para incluir la gestión del catálogo de plagas, de modo que mitori enruta consultas de plagas a botanist en lugar de caretaker.

### list_pests como herramienta de consulta directa en sensei

`list_pests` añadido a las herramientas de consulta directa de sensei (`factory.py`), de modo que "¿tengo plagas registradas?" se responde sin pasar por mitori/shokunin.

### Corrección del endpoint text-response para encuestas

`submit_text_response` en `advice.py` actualizado para aceptar `type` en `("text", "poll")`, corrigiendo fallos de test en los flujos de propuesta de plan de abonado y fitosanitario.

**Archivos clave modificados:**
- `bonsai_sensei/domain/services/templates/mitori_instruction.j2`
- `bonsai_sensei/domain/services/cultivation/species/botanist.py`
- `bonsai_sensei/domain/services/cultivation/plan/kikaru.py`
- `bonsai_sensei/domain/services/factory.py`
- `bonsai_sensei/api/advice.py`

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

## FUTURE-007 — Memoria episódica con ADK MemoryService + mem0

**Contexto:**
Los agentes Sensei no retienen conocimiento entre sesiones. Las observaciones que emergen de conversaciones (síntomas, diagnósticos, resultados de tratamientos, decisiones de cultivo) se pierden cuando termina la sesión ADK. Sin captura episódica, el keeper no puede enriquecer la wiki con conocimiento derivado de interacciones reales — solo ingesta fuentes externas (transcripciones de YouTube).

Esta feature también mitiga ISSUE-002: el reset de sesión a los 50 eventos sigue ocurriendo, pero el contexto semántico sobrevive — `PreloadMemory` lo recupera automáticamente en el turno siguiente, haciendo el reset transparente al usuario.

**Decisión de diseño:**
ADK tiene soporte nativo de memoria larga a través de `BaseMemoryService` (ver [adk.dev/sessions/memory](https://adk.dev/sessions/memory/)). El patrón correcto es implementar esta interfaz sobre [mem0](https://github.com/mem0ai/mem0) como backend self-hosted.

Evaluadas y descartadas:
- `VertexAiMemoryBankService` / `VertexAiRagMemoryService` (backends nativos ADK): cloud-only, datos salen del Ryzen 5.
- `agentmemory`: TypeScript/Rust, ecosistema incompatible.
- `Zep`: cloud-only desde abril 2025.
- `LangMem`: acoplado a LangGraph, descartado en ADR-001.
- Tools custom + inyección en `_sync_session`: subóptimo — ADK ya tiene el patrón correcto en `BaseMemoryService`.

mem0 es Python-native, self-hostable (Postgres + pgvector), mantenido activamente (v2.0.2, mayo 2026).

**Arquitectura en dos fases:**

```
Fase 1 — Memoria episódica
ADK InMemoryRunner
  └── MemoryService = Mem0MemoryService  ← custom impl de BaseMemoryService
        └── mem0 client (Postgres + pgvector, Ryzen 5)

Fase 2 — Memoria compuesta (episódica + wiki)
ADK InMemoryRunner
  └── MemoryService = CompositeMemoryService
        ├── Mem0MemoryService   ← observaciones recientes de conversaciones
        └── WikiMemoryService   ← conocimiento estructurado de la wiki (= FUTURE-002 como BaseMemoryService)
```

`BaseMemoryService` define 4 métodos:
- `add_session_to_memory(session)` — ingesta sesión completada; mem0 extrae hechos vía LLM pass
- `add_events_to_memory(events)` — opcional; ingesta incremental
- `add_memory(entry)` — opcional; inserción directa
- `search_memory(app_name, user_id, query)` — búsqueda semántica; devuelve `SearchMemoryResponse`

**Integración con el runner:**
ADK provee dos tools built-in activas cuando el runner tiene `MemoryService`:
- `PreloadMemory` — recupera contexto relevante al inicio de cada turno, sin tool call explícita
- `LoadMemory` — el agente llama cuando necesita explorar memoria activamente

La ingesta se dispara vía `after_agent_callback` al finalizar cada turno — sin cambios en `_run_agent`.

**Scope de memoria — decisión de diseño pendiente al implementar:**
Usar `user_id=telegram_id` + `agent_id=bonsai_slug`:
- Privacidad por usuario: usuario A no ve datos de B aunque tengan un bonsái con el mismo nombre.
- El keeper puede filtrar por `agent_id=bonsai_slug` para sintetizar en wiki sin mezclar usuarios.

**Flujo completo:**

```
turno completado  → after_agent_callback → Mem0MemoryService.add_session_to_memory()
                                         → mem0 extrae hechos (LLM pass interno)
turno siguiente   → PreloadMemory        → CompositeMemoryService.search_memory(query)
                                         → snippets episódicos + wiki inyectados automáticamente
keeper (cron)     → mem0 API directa     → get_all(agent_id=bonsai_slug, created_at ≥ last_run)
                                         → sintetiza → escribe wiki
```

**Límites de esta arquitectura — no elimina búsquedas directas en wiki:**
`PreloadMemory` inyecta contexto semántico en sensei al inicio del turno. Los sub-agentes (kikaru, kantei, etc.) tienen sus propios `InMemoryRunner` y no heredan este contexto. Los context builders (`load_bonsai_plan_context`, etc.) siguen siendo necesarios: cargan páginas completas y específicas para operaciones concretas dentro de los sub-agentes. `PreloadMemory` y los context builders son capas complementarias, no sustitutos.

**Infra:**
- Postgres + pgvector (aceptado; mem0 gestiona schema internamente)
- Docker Compose en Ryzen 5, sin servicio externo

**Riesgo principal:**
mem0 hace LLM pass al ingestar — puede reformular o consolidar observaciones. El keeper recibe la versión procesada, no el texto literal. Aceptable si la fidelidad semántica se mantiene; monitorizar en fase de validación.

### Orden de trabajo al implementar

**Fase 1 — Memoria episódica:**
1. Añadir pgvector a la migración de Postgres y levantar mem0 en Docker Compose
2. Implementar `Mem0MemoryService(BaseMemoryService)` wrapeando mem0 client
3. Registrar `MemoryService` en el runner de `advisor.py` y activar `PreloadMemory`
4. Configurar `after_agent_callback` para `add_session_to_memory()` al finalizar turno
5. Extender el keeper para leer mem0 con high-watermark y sintetizar en wiki
6. Tests de aceptación: observación en conversación → keeper la ingesta → página wiki actualizada

**Fase 2 — Memoria compuesta (tras completar FUTURE-002):**
7. Implementar `WikiMemoryService(BaseMemoryService)` usando el traversal de embeddings de FUTURE-002
8. Combinar en `CompositeMemoryService` que delega `search_memory()` a ambos servicios
9. Sustituir `Mem0MemoryService` por `CompositeMemoryService` en el runner

**Dependencias:**
- Fase 1: FUTURE-001 §Calidad (el keeper debe producir páginas de calidad antes de alimentarlo con observaciones conversacionales).
- Fase 2: FUTURE-002 (índice de wiki con embeddings).

---

## FUTURE-008 — Revisión de asignación de modelos: cloud vs orchestrator por agente

**Contexto:**
El sistema tiene dos modelos cloud configurables: `GEMINI_MODEL` (`gemini-3.1-flash-lite-preview` por defecto, más barato) y `GEMINI_ORCHESTRATOR_MODEL` (`gemini-3-flash-preview` por defecto, más capaz). La asignación actual es conservadora: el orchestrator solo llega a sensei, mitori y los runners de planificación interactiva (clarification, proposal, evaluate). El resto usa el modelo lite. Un análisis sistemático identifica cinco zonas donde el modelo lite produce salidas de menor calidad con impacto real en el sistema.

**Modelos actuales:**
- `cloud` = `GEMINI_MODEL` (lite, rápido, barato)
- `orchestrator` = `GEMINI_ORCHESTRATOR_MODEL` (más capaz, más caro)

### Asignaciones correctas — no cambiar

| Agente | Modelo | Razón |
|---|---|---|
| sensei | orchestrator | Root router + respuesta al usuario |
| mitori | orchestrator | Planificación estratégica con BuiltInPlanner |
| shokunin | cloud | Lee JSON del estado y despacha al AgentTool nombrado; mecánico |
| weather_advisor | cloud | Tool call simple sin razonamiento complejo |
| caretaker / nursery / gallery / storekeeper | cloud | CRUD + `limit_to_single_tool_call`; sin ambigüedad de routing |
| kantei (el agente) | cloud | Solo enruta a photo runners; el razonamiento real está en los runners |
| clarification_runner | orchestrator (heredado del manage tool) | Diálogo interactivo con el usuario |
| plan_proposal_runner | orchestrator (heredado del manage tool) | Propuesta de calendario complejo |
| evaluate_fertilization/phytosanitary | orchestrator | Análisis de adherencia al plan |

### Asignaciones incorrectas — cambiar a orchestrator

**1. `fertilizer_recommendation_runner` y `phytosanitary_recommendation_runner`**

Son el paso de razonamiento puro del patrón ADR-009: sin tools, entrada de texto → JSON con `fertilizer_name`/`treatments`, `reasoning` y `wiki_content`. Es el paso intelectualmente más exigente del sistema (razona sobre estación, historial de salud, rotación de productos) y produce un artefacto permanente escrito en la wiki. Paradoja: usan el modelo más barato mientras los runners interactivos que los rodean usan el orchestrator.

**Cambio:** propagar `orchestrator_model` desde `create_kikaru_group` a `_create_recommend_fertilizer_tool` y `_create_recommend_phytosanitary_tool` en `cultivation/plan/factory.py`.

**2. `species_wiki_compiler`**

ADR-007 establece que el compilador "decide qué buscar, cuántas veces, cómo estructurar la ficha y qué wikilinks añadir". Es síntesis creativa multi-búsqueda → wiki permanente. Una ficha de mala calidad afecta todos los consejos futuros sobre esa especie. Flash-lite genera fichas más genéricas y con menos wikilinks que un junípero y un ficus requieren distintos.

**Cambio:** recibir `orchestrator_model` en `create_botanist_group` → `create_species_wiki_compiler`. Actualmente recibe solo `model`.

**3. `wiki_keeper` (keeper agent y su runner)**

Tres fases: integrar observaciones de conversaciones → enriquecer de fichas → añadir wikilinks. Multi-step reasoning sobre conocimiento existente con múltiples tool calls de lectura/escritura. Escribe contenido permanente en la wiki. FUTURE-001 §Calidad ya documenta este problema parcialmente; esta entrada lo contextualiza en el mapa completo.

**Cambio:** `__init__.py` línea 280 pasa `model` al runner del keeper; cambiar a `orchestrator_model`. Afecta también `create_ingestion_pipeline` en `knowledge_base/ingestion/factory.py` donde todos los agentes (cleaner, extractor, channel_page_writer, keeper) reciben el mismo `model`.

**4. `photo_analysis_runner` y `photo_comparison_runner`**

Diagnóstico visual de plagas y salud. Un diagnóstico incorrecto (confundir araña roja con cochinilla) lleva a un tratamiento incorrecto. Flash-lite tiene capacidades multimodales pero el orchestrator da más detalle y precisión en identificación visual. Estos runners producen informes persistentes.

**Cambio:** propagar `orchestrator_model` desde `create_kantei_group` → `create_photo_analysis_runner` y `create_photo_comparison_runner` en `garden/kantei/factory.py`.

### Borderline — evaluar con medición

**`botanist`** — Da consejo hortícola directo al usuario. Flash-lite puede quedar corto en diagnósticos de cultivo complejos o preguntas sobre enfermedades raras. Vale la pena comparar con orchestrator bajo casos de prueba reales antes de decidir.

**`kikaru`** — Enruta entre 10+ tools de plan. `limit_to_single_tool_call` activo: un error de routing no se autocorrige. Borderline hacia orchestrator si se observan errores de routing frecuentes.

**`card_extractor` (ingestion)** — Extrae conocimiento de transcripts de vídeo. La calidad de extracción afecta directamente la calidad de las fichas y por tanto la wiki. Candidato a orchestrator si la calidad del keeper mejorada (punto 3) no es suficiente.

### Patrón de implementación

El patrón `effective_orchestrator_model = orchestrator_model or model` ya está establecido en `factory.py` y `cultivation/plan/factory.py`. Para cada runner afectado:
1. Añadir `orchestrator_model: object = None` al factory que crea el runner.
2. Calcular `effective_orchestrator_model = orchestrator_model or model`.
3. Pasar `effective_orchestrator_model` al runner en lugar de `model`.
4. Propagar `orchestrator_model` hacia arriba por la cadena de factories hasta `create_sensei_agent` en `agents_factory.py` (que ya recibe `orchestrator_model`).

### Orden de trabajo al implementar

1. `fertilizer_recommendation_runner` y `phytosanitary_recommendation_runner` (mayor impacto en calidad de consejos, menor radio de cambio)
2. `wiki_keeper` (resolver junto con FUTURE-001 §Calidad)
3. `photo_analysis_runner` y `photo_comparison_runner`
4. `species_wiki_compiler`
5. Medir `botanist` y `kikaru` antes de decidir

**Dependencia con FUTURE-001:** el punto 3 (wiki_keeper) cubre el mismo problema que FUTURE-001 §Calidad paso 1 — usar un modelo más potente en el keeper. Esta entrada proporciona el contexto completo y el plan de implementación específico; FUTURE-001 §Orden de trabajo puede actualizarse para referenciar FUTURE-008 cuando se retome.
