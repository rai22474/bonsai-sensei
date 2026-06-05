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

## FUTURE-007 — Traversal por grafo en el índice wiki

**Contexto:**
FalkorDB almacena los links entre páginas como edges `[:LINKS_TO]` (poblados desde `IndexEntry.links` al indexar). La búsqueda actual es plana (KNN top-k). El traversal añadiría páginas relacionadas por enlace a los resultados del KNN, sin coste extra de embeddings.

**Implementación:** en `wiki_index/searcher.py`, extender `create_search_by_embedding` con opción de traversal:

```cypher
CALL db.idx.vector.queryNodes('WikiPage', 'embedding', 5, vecf32($embedding))
YIELD node AS seed, score
MATCH (seed)-[:LINKS_TO*1..2]->(related:WikiPage)
WHERE NOT related.page_path IN [seed.page_path]
RETURN DISTINCT related.page_path, related.abstract
ORDER BY score DESC LIMIT 10
```

**Dependencia:** ninguna — FalkorDB y los edges `[:LINKS_TO]` ya están en producción. Suficiente con <500 páginas sin traversal, pero el grafo ya está listo.

---

## FUTURE-008 — Auto-detección de canal desde URL de YouTube

**Contexto:**
Al ingerir un video via Telegram (`/ingest <url>` o enviando la URL directamente), el admin debe especificar el canal manualmente como segundo argumento. Sin él, se usa `WIKI_DEFAULT_CHANNEL` ("general"), lo que mezcla todos los videos en un único directorio.

**Objetivo:**
Cuando no se proporciona canal, resolverlo automáticamente desde los metadatos del video (campo `uploader_id` de `yt-dlp`) y normalizarlo a slug: `@BonsaiEmpire` → `bonsaiempire`.

**Implementación:**
- `pyproject.toml`: añadir `yt-dlp`
- `ingestion/transcript_loader.py`: añadir `create_channel_resolver(ydl_opts_factory) -> Callable[[str], str]` — extrae `uploader_id`, normaliza a lowercase slug
- `telegram/handle_admin_ingest.py`: añadir param `resolve_channel: Callable | None`; si no hay canal en el mensaje, llamarlo antes de ingestar
- `telegram/admin_bot.py`: inyectar `resolve_channel` en los handlers de ingest vía `partial`
- `main.py`: crear `resolve_channel = create_channel_resolver(lambda: {"quiet": True, "skip_download": True})` y pasarlo al `AdminBotManager`

**Trade-off:** `yt-dlp` hace una petición HTTP extra (~1-2 s) antes de responder al admin. Aceptable dado que la ingestión ya tarda varios segundos.

---

## FUTURE-009 — Ingestión de PDFs (libros y textos técnicos)

**Contexto:**
El pipeline actual solo acepta transcripciones de YouTube. Para enriquecer la wiki con libros o textos técnicos de bonsái en PDF, se necesita una ruta de ingestión alternativa que salte los pasos específicos de YT (descarga + limpieza LLM) e inyecte directamente en `transcripts/clean/`.

**Diseño:**

Pipeline propuesto:
```
PDF → text extraction → chunks → transcripts/clean/<source>/<book_slug>_NNN.md → card extractor (sin cambios) → dreamer (sin cambios)
```

- Card extractor, dreamer y wiki_index no requieren cambios.
- Chunking fijo (~40 páginas por chunk) con `pypdf` — simple y determinista. Los TOC de PDFs escaneados no son fiables.
- `<source>` es un slug que identifica la colección (e.g., `libros`, `bonsai-today`).

**Decisión pendiente:** trigger de ingestión.
- Opción A: admin Telegram — subir PDF al chat admin, coherente con `/ingest <url>` actual.
- Opción B: `POST /ingest/pdf` con path local al PDF — útil para lotes.
- Opción C: script CLI `python -m knowledge_base.ingestion.pdf_ingest <file>` — más simple para uso puntual.

**Implementación (una vez decidido el trigger):**
- `pyproject.toml`: añadir `pypdf`
- `ingestion/pdf_loader.py`: `create_pdf_chunker(chunk_size_pages) -> Callable[[Path, str, Path], list[Path]]` — extrae texto por páginas, agrupa en chunks, guarda en `transcripts/clean/<source>/<slug>_NNN.md`
- `ingestion/factory.py`: añadir `create_pdf_ingester`
- Trigger según opción elegida
