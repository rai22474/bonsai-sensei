# FUTURE-007 — Plan de implementación: Memoria episódica

Referencia: [FUTURE-007 en future-work.md](future-work.md)

---

## Fase 0 — Infra (prerequisito)

**Archivos:** `docker-compose.yml`, `pyproject.toml`

1. Cambiar imagen Postgres: `postgres:15-alpine` → `pgvector/pgvector:pg15`
2. Añadir `mem0ai[postgres]` a `pyproject.toml` dependencies
3. Añadir env var `MEM0_DB_URL` a `docker-compose.yml` (puede reutilizar `DATABASE_URL` o schema separado)

**Aceptación:** `CREATE EXTENSION vector;` ejecuta sin error en el contenedor.

---

## Fase 1 — `Mem0MemoryService`

**Archivo nuevo:** `bonsai_sensei/memory/mem0_memory_service.py`

Implementar `BaseMemoryService` (4 métodos):

```python
class Mem0MemoryService(BaseMemoryService):
    async def add_session_to_memory(self, session): ...  # → mem0.add(messages, user_id, agent_id)
    async def search_memory(self, app_name, user_id, query): ...  # → mem0.search() → SearchMemoryResponse
    async def add_events_to_memory(self, events): ...   # no-op en Fase 1
    async def add_memory(self, entry): ...              # no-op en Fase 1
```

Scope de memoria: `user_id=telegram_id`, `agent_id=bonsai_slug` extraído de session metadata si existe.

**Test unitario:** mock mem0 client, verificar que `add_session_to_memory` llama mem0 con parámetros correctos y que `search_memory` devuelve `SearchMemoryResponse` bien formado.

---

## Fase 2 — Integración con el runner ADK

**Archivo:** `bonsai_sensei/domain/services/advisor.py`

Tres cambios en `create_advisor`:

```python
memory_service = Mem0MemoryService(...)

runner = InMemoryRunner(
    agent=sensei_agent,
    app_name="bonsai_sensei",
    memory_service=memory_service,   # nuevo
)
```

Añadir `after_agent_callback` al agente sensei (en `sensei.py` o `create_sensei`) para llamar `memory_service.add_session_to_memory(session)` tras cada turno.

`PreloadMemory` se activa automáticamente al registrar el `MemoryService` — no requiere cambios en tools de sensei.

**Verificar:** ISSUE-002 mitigado. Conversación de 6+ turnos con tool calls → reset de sesión → siguiente turno recupera contexto de mem0 automáticamente.

---

## Fase 3 — Integración con el keeper

**Archivos:** `bonsai_sensei/knowledge_base/keeper/runner.py`, `bonsai_sensei/knowledge_base/keeper/tools.py`

**Archivo nuevo:** `bonsai_sensei/knowledge_base/keeper/memory_reader.py`

```python
def read_new_observations(bonsai_slug: str, since: datetime) -> list[str]:
    return mem0_client.get_all(
        agent_id=bonsai_slug,
        filters={"created_at": {"gte": since.isoformat()}}
    )
```

Persistir `last_run` por bonsái: campo en DB (`BonsaiMemorySync`) o fichero `wiki/memory-sync.json`.

Extender el runner del keeper para:
1. Leer observaciones nuevas de mem0 por bonsái
2. Pasarlas como contexto adicional al agente keeper
3. Actualizar `last_run` tras síntesis exitosa

**Aceptación:** test de integración — observación en mem0 → keeper la lee → página wiki actualizada.

---

## Fase 4 — Test de aceptación end-to-end

Escenario BDD:
```
Given bonsái "Hanako" existe
When usuario reporta "hojas amarillas en el ápice"
And keeper ejecuta su ciclo
Then la página wiki de Hanako contiene referencia a clorosis en ápice
```

- `given`: REST API
- `when`: `advise()` + ciclo keeper
- `then`: REST GET wiki page

---

## Fase 5 — `WikiMemoryService` + `CompositeMemoryService` *(tras FUTURE-002)*

**Prerequisito:** FUTURE-002 implementado (`wiki-index/` con embeddings JSON por página).

**Archivos nuevos:**
- `bonsai_sensei/memory/wiki_memory_service.py` — `search_memory()` usa traversal coseno de FUTURE-002
- `bonsai_sensei/memory/composite_memory_service.py` — delega a ambos servicios, fusiona resultados

Sustituir `Mem0MemoryService` por `CompositeMemoryService` en `advisor.py`. `PreloadMemory` inyecta episódico + wiki sin cambios en sensei.

```python
class CompositeMemoryService(BaseMemoryService):
    async def search_memory(self, app_name, user_id, query):
        episodic = await self.mem0_service.search_memory(app_name, user_id, query)
        wiki     = await self.wiki_service.search_memory(app_name, user_id, query)
        return merge(episodic, wiki)
```

---

## Orden de ejecución

```
Fase 0 → Fase 1 → Fase 2 → Fase 3 → Fase 4
                                          ↓
                              (pausa hasta FUTURE-002)
                                          ↓
                                       Fase 5
```

## Decisiones pendientes al arrancar

- Confirmar API exacta de `InMemoryRunner` para `memory_service` param (verificar ADK >= 1.32)
- Confirmar nombre del callback ADK para post-turno (`after_agent_callback` o equivalente)
- Decidir backend de `last_run`: DB table `BonsaiMemorySync` vs fichero `wiki/memory-sync.json`
