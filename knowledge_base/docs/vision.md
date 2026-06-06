# Visión del Servicio

El servicio `knowledge_base` transforma fuentes de conocimiento externas (transcripciones de YouTube, observaciones conversacionales) en una wiki estructurada y mantenida automáticamente. Su rol en el sistema es ser el repositorio de conocimiento general sobre bonsáis — especies, técnicas, enfermedades, protocolos — que enriquece las respuestas del agente sensei.

## Principio de diseño

La wiki es la fuente de verdad para conocimiento general. El keeper la mantiene de forma autónoma; el ciclo de revisión humana garantiza que ningún cambio llega a producción sin supervisión. Los agentes sensei consumen la wiki via MCP o búsqueda semántica — no acceden directamente a las fuentes originales.

## Componentes principales

- **Ingestion pipeline** — descarga y normaliza transcripciones de YouTube por canal
- **Dreamer** — orquestador de síntesis que extrae tarjetas de conocimiento de las transcripciones
- **Keeper** — agente ADK que mantiene la wiki a partir de las tarjetas; escribe y actualiza páginas
- **Wiki editor** — tools de lectura/escritura de páginas wiki con historial git
- **Wiki index** — índice semántico de la wiki con embeddings para búsqueda por similitud
- **MCP server** — expone la wiki al agente sensei vía Model Context Protocol

## Casos de uso no implementados aún

- **Revisión humana post-keeper** (FUTURE-001): canal Telegram admin donde el operador revisa y aprueba cada página antes de considerarla definitiva.
