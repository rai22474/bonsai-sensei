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

## FUTURE-004 — Migrar el índice wiki a FalkorDB

**Contexto:**
El índice wiki actual (`wiki_index/`) almacena embeddings en disco como JSON + arrays numpy. Funciona bien para <500 páginas (búsqueda plana en microsegundos), pero no soporta traversal por grafo. FalkorDB ya corre en producción (`docker-compose.yml`) para el servicio `episodic_memory`; el coste operacional es cero.

Se verificó que la imagen `falkordb/falkordb:latest` soporta:
- `CREATE VECTOR INDEX` con `{dimension: 3072, similarityFunction: 'cosine'}`
- `CALL db.idx.vector.queryNodes(...)` para KNN
- `MATCH ()-[:LINKS_TO*1..N]->()` para traversal multi-hop

Esto desbloquea el traversal pendiente de FUTURE-002 como una query Cypher de una línea, en vez de ~80 líneas de beam-search en Python sobre JSON.

**Dependencia:** ninguna (FalkorDB ya en producción).

### Schema propuesto

```cypher
(:WikiPage {page_path, title, abstract, embedding: vecf32[3072]})
(:WikiPage)-[:LINKS_TO]->(:WikiPage)

CREATE VECTOR INDEX FOR (n:WikiPage) ON (n.embedding)
  OPTIONS {dimension: 3072, similarityFunction: 'cosine'}
```

Un nodo por página wiki. Las relaciones `[:LINKS_TO]` se crean a partir de `IndexEntry.links` (ya poblado).

### Qué cambia en el código

**`wiki_index/store.py`** — reemplazar lectura/escritura de JSON por Cypher:
- `save_entry(entry)` → `MERGE (:WikiPage {page_path:$path}) SET node.embedding=..., node.title=...` + `MERGE [:LINKS_TO]` por cada link
- `load_entry(path)` → `MATCH (:WikiPage {page_path:$path})`
- `load_all_entries()` → `MATCH (n:WikiPage) RETURN n`
- Inyectar `falkordb.Graph` como dependencia (patrón CLAUDE.md). No instanciar dentro.
- Desaparece el directorio `wiki-index/` del disco y su entrada en `.gitignore`.

**`wiki_index/searcher.py`** — reemplazar numpy por KNN nativo:
```cypher
CALL db.idx.vector.queryNodes('WikiPage', 'embedding', $k, vecf32($embedding))
YIELD node, score
RETURN node.page_path, node.title, score
```
- Elimina `numpy` del paquete.
- `Graph` inyectado como dep.

**`wiki_index/indexer.py`** — sin cambios estructurales. Llama `save_entry` via inyección; el store subyacente cambia, el indexer no.

**`wiki_index/entry.py`** — sin cambios. `IndexEntry` sigue siendo el modelo de dominio.

**Traversal FUTURE-002 (una vez migrado):**
```cypher
CALL db.idx.vector.queryNodes('WikiPage', 'embedding', 5, vecf32($embedding))
YIELD node AS seed, score
MATCH (seed)-[:LINKS_TO*1..2]->(related:WikiPage)
WHERE NOT related.page_path IN [seed.page_path]
RETURN DISTINCT related.page_path, related.title
ORDER BY score DESC
LIMIT 10
```

### Configuración

Variable de entorno necesaria (ya existe en `docker-compose.yml` para `episodic_memory`):
```
FALKORDB_HOST=falkordb
FALKORDB_PORT=6379
WIKI_INDEX_GRAPH=wiki_index   ← nombre del grafo, separado del grafo de episodic_memory
```

`knowledge_base/pyproject.toml` — añadir `falkordb>=1.0`.

### Orden de trabajo al retomar

1. Añadir `falkordb>=1.0` a `knowledge_base/pyproject.toml`
2. Añadir `WIKI_INDEX_GRAPH` a `docker-compose.yml` y `.env.example`
3. Reescribir `wiki_index/store.py` con DI de `falkordb.Graph`
4. Reescribir `wiki_index/searcher.py` con KNN Cypher
5. Actualizar `wiki_index/__init__.py` y `main.py` para construir el `Graph` y pasarlo como dep
6. Eliminar `wiki-index/` de `.gitignore` (ya no existe caché en disco)
7. Reconstruir el índice completo: `POST /api/wiki/index/rebuild`
8. Implementar traversal FUTURE-002 en `searcher.py` como query Cypher combinada
