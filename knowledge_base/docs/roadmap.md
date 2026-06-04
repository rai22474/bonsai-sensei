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

## FUTURE-003 — Formalizar reglas de enlazado en el keeper

**Contexto:**
La taxonomía ya existe en la wiki (`species/`, `techniques/`, `pests/`, `fertilizers/`, `products/`). Las páginas YA enlazan correctamente en la práctica — la Phase 2 del dreamer genera wikilinks. Lo que falta es formalizar las reglas en el prompt del keeper y del wiki editor para que sean consistentes y no dependan del LLM "acertando" solo.

**Dependencia:** FUTURE-002 (implementado).

### Taxonomía real (ya en producción)

```
wiki/
  bonsai/           ← instancias (bonsai/eren, bonsai/itachi, ...)
  species/          ← una página por especie (10 páginas)
  techniques/       ← una página por técnica (abonado, alambrado, defoliacion, ...)
  pests/            ← plagas (14 páginas: acaros, pulgones, cochinilla, ...)
  fertilizers/      ← productos fertilizantes (biogold, hanagokoro, ...)
  products/         ← productos de tratamiento (trichoderma, acidos-humicos, ...)
  enfermedades/     ← enfermedades fúngicas/patológicas (1 stub vacío — necesita contenido)
```

Reglas invariantes (ya se respetan en práctica, falta codificarlas):
- Una página por concepto, nombres en minúsculas con guiones
- `bonsai/` enlaza a conocimiento general; conocimiento general NO enlaza a instancias específicas

### Qué falta

**1. Reglas explícitas de enlazado en el prompt del dreamer** (`dreamer/agent.py` Phase 2):

La Phase 2 actual es genérica. Añadir:
- Página de especie → debe enlazar a: plagas frecuentes (`pests/`), técnicas aplicables (`techniques/`), fertilizantes recomendados (`fertilizers/`)
- Página de bonsái → debe enlazar a: su página de especie (`species/`)
- Página de plaga → debe enlazar a: productos de tratamiento (`products/`, `phytosanitaries/`), especies afectadas (`species/`)
- Página de técnica → debe enlazar a: especies en las que es especialmente relevante, plagas que previene o trata

**2. Instrucciones de enlazado en el wiki editor** (`wiki_editor/agent.py`):

El wiki editor actualmente no tiene ninguna instrucción sobre enlaces. Añadir las mismas reglas que al dreamer para que las correcciones manuales respeten la taxonomía.

**3. Poblar `enfermedades/`**:

`enfermedades/hongos-raiz.md` existe pero está vacío. Crear contenido o eliminarlo. Decidir si `enfermedades/` y `pests/` son secciones distintas (patologías vs plagas) o si se fusionan.

### Orden de trabajo al retomar
1. Decidir `enfermedades/` vs `pests/` — ¿secciones separadas o fusionar en `diseases/`?
2. Actualizar Phase 2 del dreamer con reglas de enlazado explícitas
3. Añadir instrucciones de enlazado al wiki editor
4. Validar con un bonsái real: traversal desde `bonsai/X/index.md` → `species/` → `pests/` → `products/`
