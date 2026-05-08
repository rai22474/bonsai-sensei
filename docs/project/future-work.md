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
