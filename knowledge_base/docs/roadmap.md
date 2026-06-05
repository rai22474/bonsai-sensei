# Roadmap

Iniciativas pendientes que aún no están listas para implementar. Consultar antes de empezar tareas relacionadas.

---

## FUTURE-001 — Calidad del dreamer (bucle crítico/autocrítica)

**Contexto:**
El flujo de revisión humana está implementado: canal admin Telegram, notificación post-keeper con lista de páginas, sesión de revisión con estado pending/confirmed/reverted, tools `get_page_diff` y `revert_page`, persistencia entre reinicios. Ver `telegram/admin_bot.py`, `wiki_review_session.py`, `api/wiki_review.py`, `wiki_git.py`.

Lo que falta es la capa de calidad autónoma del dreamer antes de que los cambios lleguen al admin.

**Pendiente:**
- Bucle crítico/autocrítica en el dreamer: generar → evaluar → refinar → escribir
- El dreamer ya usa `gemini-3-flash-preview` (`GEMINI_ORCHESTRATOR_MODEL`) con `_MAX_LLM_CALLS=100`. Los agentes auxiliares usan `gemini-3.1-flash-lite-preview` — correcto.
- Diseño: un agente evaluador lee el borrador de página y emite críticas estructuradas; el orquestador refina hasta que el evaluador aprueba o se alcanza el límite de iteraciones.

---

## FUTURE-002 — Índice semántico de la wiki con embeddings ✅ IMPLEMENTADO (2026-05-25)

**Estado:** Implementado y en producción.

**Implementación:**
- `wiki_index/` — paquete completo (embedder, entry, store, searcher, indexer)
- Modelo: `gemini-embedding-001` (3072 dims)
- `wiki-index/` en `.gitignore` — caché regenerable
- El dreamer y el wiki editor actualizan el índice al escribir páginas
- El agente sensei tiene la tool `search_wiki_knowledge` (top-5)
- `POST /api/wiki/index/rebuild` para reconstrucción vía REST

**Pendiente:**
- Traversal por grafo (seguir links con poda por similitud) no implementado — búsqueda plana suficiente para <500 páginas. Los links están indexados en `IndexEntry.links` pero el searcher no los sigue. Implementar en `wiki_index/searcher.py`.

---

## FUTURE-003 — Formalizar reglas de enlazado en el keeper ✅ IMPLEMENTADO (2026-06-04)

**Estado:** Implementado.

**Implementación:**
- `pests/` y `enfermedades/` fusionados en `diseases/` (12 páginas). `hongos-raiz.md` migrado. Duplicados con encoding roto eliminados.
- Dreamer instruction migrada a Jinja2 (`dreamer/templates/dreamer_instruction.jinja2`). Phase 0 añade regla de enlace bonsai→species. Phase 2 añade reglas de enlazado direccionales por tipo de página.
- Wiki editor instruction actualizada con sección `## Taxonomía de la wiki` con reglas de enlazado.
- `dreamer-processed-wikilinks.json` limpiado para forzar re-evaluación de wikilinks con las nuevas reglas.

### Taxonomía actual

```
wiki/
  bonsai/           ← instancias (bonsai/eren, bonsai/itachi, ...)
  species/          ← una página por especie
  techniques/       ← una página por técnica (abonado, alambrado, defoliacion, ...)
  diseases/         ← plagas y enfermedades (ácaros, cochinillas, roya, hongos-raiz, ...)
  fertilizers/      ← fertilizantes (biogold, hanagokoro, ...)
  products/         ← productos de tratamiento (trichoderma, acidos-humicos, ...)
  phytosanitaries/  ← fitosanitarios (azufre, cobre, ...)
```

Reglas invariantes:
- Una página por concepto, nombres en minúsculas con guiones
- `bonsai/` enlaza a conocimiento general; conocimiento general NO enlaza a instancias específicas

**Pendiente:**
- Reconstruir el índice semántico tras la migración: `POST /api/wiki/index/rebuild` (las entradas de `pests/` en el índice están obsoletas).

---

## FUTURE-005 — Mejorar la instrucción del agente de fichas (cards phase) ✅ IMPLEMENTADO (2026-06-05)

**Estado:** Implementado.

**Implementación:**
- `dreamer/tools.py`: `create_search_wiki_knowledge_tool(embed, search_by_embedding)` — sustituye `list_wiki_pages` en el cards agent; busca por semántica en vez de adivinar slugs desde listado
- `dreamer/cards_agent.py`: factory acepta `embed` + `search_by_embedding` opcionales; usa `search_wiki_knowledge` si están presentes, fallback a `list_wiki_pages` si no
- `dreamer/templates/cards_instruction.jinja2`: reescrito con los 7 fixes — taxonomía completa (añade `diseases/`, `phytosanitaries/`), búsqueda semántica, secciones canónicas por tipo de página, reglas de slug, granularidad, formato canónico de `## Fuentes`, regla `bonsai/` vs conocimiento general
- `main.py`: `create_cards_agent` recibe `embed=embed_text` y `search_by_embedding=app.state.search_by_embedding`
- `dreamer/runner.py`: `_MAX_LLM_CALLS_WIKILINKS` 20 → 50; `_run_phase` captura `LlmCallsLimitExceededError` con warning (la fase wikilinks ya no crashea el dreamer si alcanza el límite)

---

## FUTURE-004 — Migrar el índice wiki a FalkorDB ✅ IMPLEMENTADO (2026-06-05)

**Estado:** Implementado. Índice reconstruido en producción.

**Implementación:**
- `wiki_index/store.py` reescrito: `initialize_schema`, `create_save_entry`, `create_load_entry`, `create_load_all_entries` — todos con `falkordb.Graph` como dependencia inyectada
- `wiki_index/searcher.py` reescrito: `create_search_by_embedding` usa KNN Cypher (`db.idx.vector.queryNodes`); convierte distancia a similitud (`1 - score`)
- `wiki_index/indexer.py`: `save_entry: Callable` como parámetro en `update_page_index` y `build_full_index`
- `dreamer/runner.py`, `wiki_editor/runner.py`, `telegram/admin_bot.py`, `api/wiki_index.py`: propagación de `save_entry` por DI
- `main.py`: crea `falkordb.Graph`, llama `initialize_schema`, enlaza callables en `app.state`
- `pyproject.toml`: `falkordb>=1.0` añadido, `numpy` eliminado
- `docker-compose.yml` y `tests/acceptance/docker-compose.acceptance.yml`: `FALKORDB_HOST`, `FALKORDB_PORT`, `WIKI_INDEX_GRAPH`, `depends_on: falkordb`

**Pendiente:**
- Traversal por grafo FUTURE-002: query Cypher `[:LINKS_TO*1..2]` desde seed nodes del KNN. Implementar en `wiki_index/searcher.py` como opción de `search_by_embedding`.
