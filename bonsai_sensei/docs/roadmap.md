# Trabajo futuro

Iniciativas pendientes que aún no están listas para implementar. Consultar antes de empezar tareas relacionadas.

---

## FUTURE-004 — Índice wiki en sub-agentes (kantei, storekeeper)

**Contexto:**
El agente sensei tiene `search_wiki_knowledge` (búsqueda semántica top-5 sobre el índice de `knowledge_base`). Los sub-agentes (kantei, storekeeper) no la tienen — operan sin acceso al conocimiento general de la wiki.

**Pendiente:**
- Añadir `search_wiki_knowledge` a kantei: el diagnóstico de salud mejoraría con acceso a páginas de enfermedades y técnicas de tratamiento.
- Añadir `search_wiki_knowledge` a storekeeper si necesita consultar protocolos de abonado o fitosanitarios.
- El HTTP client ya existe en `bonsai_sensei/infrastructure/wiki_client.py` — solo hay que inyectarlo en los context builders de cada sub-agente.

**Dependencia:** `knowledge_base` ISSUE-KB-001 (MCP devuelve vacío) no afecta — sensei usa HTTP client, no MCP.

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

## FUTURE-010 — Plan de diseño orientado a objetivo

**Contexto:**
El sistema gestiona actualmente trabajos de cultivo rutinarios (fertilización, fitosanitarios, trasplante) a través de kikaru. Pero el desarrollo artístico de un bonsái requiere un tipo diferente de planificación: el usuario tiene un objetivo de diseño concreto ("desarrollar nebari más ancha", "afinar ápice", "dar movimiento al primer tramo", "conseguir ramas secundarias definidas") y necesita que el sistema le ayude a trazar la secuencia de técnicas específicas para llegar a ese objetivo.

Este caso de uso está identificado en `vision.md` como "Generación de plan estándar por especie/diseño" y debe seguir el patrón de **agente libre** (no mitori/shokunin), por ser una planificación multi-turno con decisiones adaptadas al estado actual del árbol.

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
- opcionalmente: búsqueda de técnicas en base de conocimiento (ver `knowledge_base/docs/future-work.md` FUTURE-002/003)

El agente conduce una conversación para entender el objetivo, el estado actual del árbol y las limitaciones del usuario (tiempo disponible, nivel de experiencia), y produce el plan adaptado.

**Vínculo con vision.md:**
Cubre directamente el caso de uso "Generación de plan estándar por especie/diseño". Implementar después de FUTURE-002 si se quiere que el agente consulte la base de conocimiento de técnicas; puede implementarse antes si se apoya solo en el conocimiento del modelo.
