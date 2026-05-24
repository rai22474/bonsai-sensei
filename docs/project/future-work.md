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
El keeper escribe páginas de forma autónoma. Se requiere un paso de revisión por el administrador antes de que los cambios se consideren definitivos.

**Diseño resuelto: canal Telegram de administración + sesión ADK por página.**

El canal admin es un grupo privado de Telegram separado del canal de usuarios, configurado via `ADMIN_TELEGRAM_CHAT_ID`. El mismo bot atiende ambos canales; los mensajes del canal admin se enrutan a una sesión ADK con `user_id=admin` que tiene acceso a tools de wiki y git.

**Flujo de revisión tras cada ejecución del keeper:**

```
Keeper termina → git commit local → bot notifica al canal admin:
  "3 páginas actualizadas:
   • bonsai/goku/index.md
   • species/ficus-retusa.md
   • techniques/wiring.md"
  [Botones inline por página]

Admin toca una página →
  Agente presenta resumen del diff (LLM sobre git diff)
  Conversación libre: explorar, preguntar, editar
  Admin decide → [✅ Confirmar] [↩️ Revertir]

  Si Confirmar → página sale de pendientes, se presenta lista restante
  Si Revertir  → git checkout HEAD~1 -- <path> + nuevo commit, página sale de pendientes

→ "2 páginas pendientes: ..." → siguiente ciclo
→ "Revisión completada ✓"
```

**Reglas de UX:**
- Una página a la vez: foco y decisión explícita antes de pasar a la siguiente.
- El admin puede volver a una página ya confirmada en cualquier momento ("muéstrame goku otra vez") — puede revertirla aunque esté confirmada.
- Aprobación implícita si el admin no inicia revisión en N horas (el commit ya está, no se requiere acción).
- El diff se muestra como resumen LLM, no como raw `git diff` — Telegram no maneja diffs largos bien.

**Tools nuevas necesarias en el agente admin:**
- `get_wiki_page_diff(page_path)` → resumen LLM de `git diff HEAD~1 -- <path>`
- `revert_wiki_page(page_path)` → `git checkout HEAD~1 -- <path>` + nuevo commit de revert

**Estado de la sesión de revisión** (guardado en `app.state` por `review_session_id`):
```python
{
  "commit_hash": "abc123",
  "pending": ["bonsai/goku/index.md", "species/ficus-retusa.md"],
  "confirmed": [],
  "reverted": [],
  "current_page": None,
}
```

### Descubrimiento de páginas del keeper
Los agentes Sensei descubren páginas wiki a través del `wiki_path` almacenado en la base de datos. Las páginas creadas por el keeper no están registradas en la base de datos, por lo que los agentes no pueden encontrarlas. Este problema se resuelve con el índice de navegación descrito en FUTURE-002 — no requiere infraestructura adicional.

### Orden de trabajo al retomar
1. Mejorar la calidad de salida del keeper (modelo + llamadas, o bucle crítico)
2. Git local para la wiki (historial + rollback + `git init` en `WIKI_PATH`)
3. Canal admin de Telegram: notificación post-keeper con lista de páginas cambiadas
4. Tools `get_wiki_page_diff` y `revert_wiki_page` en el agente admin
5. Sesión ADK para el canal admin con estado de revisión en `app.state`
6. Índice de navegación (FUTURE-002) — permite a los agentes encontrar páginas del keeper

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

## FUTURE-010 — Plan de diseño orientado a objetivo

**Contexto:**
El sistema gestiona actualmente trabajos de cultivo rutinarios (fertilización, fitosanitarios, trasplante) a través de kikaru. Pero el desarrollo artístico de un bonsái requiere un tipo diferente de planificación: el usuario tiene un objetivo de diseño concreto ("desarrollar nebari más ancha", "afinar ápice", "dar movimiento al primer tramo", "conseguir ramas secundarias definidas") y necesita que el sistema le ayude a trazar la secuencia de técnicas específicas para llegar a ese objetivo.

Este caso de uso está identificado en `docs/project/vision.md` como "Generación de plan estándar por especie/diseño" y debe seguir el patrón de **agente libre** (no mitori/shokunin), por ser una planificación multi-turno con decisiones adaptadas al estado actual del árbol.

**¿Qué diferencia este plan de los trabajos de kikaru?**
Kikaru programa trabajos ya decididos por el usuario: "quiero fertilizar el día X". El plan de diseño responde a "¿qué tengo que hacer para conseguir Y?". El agente razona sobre el estado del árbol, la especie, la época del año y el objetivo, y genera una secuencia de técnicas con justificación y ventana temporal.

**Técnicas a contemplar:**
- Alambrado (wiring): dirección de ramas, momento óptimo según especie (otoño/invierno para caducifolias, evitar crecimiento activo)
- Pinzado (pinching): control de elongación, favorece ramificación fina
- Defoliado: reducción de tamaño de hoja, apertura de luz interior — solo especies que lo toleran
- Poda de mantenimiento / poda estructural: eliminación de ramas sacrificadas, inversas, cruzadas
- Poda de engrosamiento / jin / shari: técnicas de deadwood
- Trasplante con trabajo de raíces: nebari, reducción de raíces gruesas
- Nebari: guías de raíces aéreas, exposición progresiva

**Modelo de dominio (por resolver):**

Dos opciones a evaluar al implementar:

**Opción A — Entidad `DesignObjective` en base de datos:**
```
DesignObjective:
  id, bonsai_id, objective (text), created_at, achieved_at (nullable)

DesignWork (extends PlannedWork o entidad separada):
  id, objective_id, technique, rationale, window_start, window_end, status
```
Ventaja: trazabilidad, progreso cuantificable, filtros por estado.
Desventaja: más tablas, más APIs REST, mayor coste de implementación.

**Opción B — Plan como página wiki del bonsái:**
El agente escribe un plan de diseño en `wiki/bonsai/<nombre>/design-plan.md` con secciones por técnica, ventana temporal y estado. Progreso se actualiza conversacionalmente o via keeper.
Ventaja: simplicidad, integración natural con wiki existente, el agente puede leer y actualizar en lenguaje natural.
Desventaja: sin datos estructurados, difícil de consultar programáticamente, sin reminder scheduling.

**Recomendación:** empezar con Opción B (wiki) para validar el flujo sin infraestructura adicional. Migrar a Opción A si se necesita scheduling de recordatorios (integración con kikaru) o consultas estructuradas.

**Patrón de agente:**
Agente libre con acceso a:
- herramienta de lectura/escritura de wiki (ya existe)
- herramienta de consulta del bonsái y su historial (ya existe)
- herramienta de consulta de especie (herbarium, ya existe)
- opcionalmente: búsqueda de técnicas en base de conocimiento (FUTURE-002/003)

El agente conduce una conversación para entender el objetivo, el estado actual del árbol y las limitaciones del usuario (tiempo disponible, nivel de experiencia), y produce el plan adaptado.

**Vínculo con vision.md:**
Cubre directamente el caso de uso "Generación de plan estándar por especie/diseño". Implementar después de FUTURE-002 si se quiere que el agente consulte la base de conocimiento de técnicas; puede implementarse antes si se apoya solo en el conocimiento del modelo.
