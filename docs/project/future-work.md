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

## FUTURE-004 — Eventos de plaga por bonsái (parcialmente completado)

**Contexto:**
El sistema registra tratamientos fitosanitarios (`apply_phytosanitary`) y planes fitosanitarios, pero no tiene forma de registrar una observación de plaga como evento independiente. Sin este registro no hay trazabilidad infección → tratamiento, ni historial de plagas por bonsái para informar futuras recomendaciones.

**Estado (2026-05-18):** Catálogo `Pest` implementado y flujo básico de detección completado: migración, REST endpoints, generación LLM al alta de especie, páginas wiki, `list_pests` en sensei, herramienta `create_pest_event` en caretaker con confirmación, tests de aceptación verdes. Integración Tavily para búsqueda fitosanitaria online implementada (FUTURE-004b). Propuesta de revisión de plan reemplazada por aviso pasivo en texto (ver paso 6). Pendiente: enlace a `apply_phytosanitary`.

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
2. ~~Store functions + REST endpoints para `Pest` y `PestEvent`~~ (done — `Pest` solo; `PestEvent` pendiente)
3. ~~Generación de catálogo de plagas al alta de especie (LLM + wiki, re-ejecutable)~~ (done)
4. ~~Herramienta de agente: alta de `PestEvent` con confirmación~~ (done — versión básica; selección filtrada por especie pendiente)
5. Enlace a `apply_phytosanitary` desde el evento
6. ~~Propuesta de revisión de plan si hay uno activo~~ — reemplazado por aviso pasivo: `create_pest_event` devuelve `active_plan: bool`; caretaker lo menciona en texto sin preguntar. Ver ADR-011 para el razonamiento.
7. ~~Tests de aceptación (detectar + confirmar, plaga no registrada)~~ (done 2026-05-15)

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
