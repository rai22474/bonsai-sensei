# Visión del Servicio

El servicio `episodic_memory` proporciona memoria persistente entre sesiones para el agente sensei. Implementa la interfaz `BaseMemoryService` de Google ADK sobre Graphiti, permitiendo que observaciones extraídas de conversaciones (síntomas, diagnósticos, decisiones de cultivo) sobrevivan al reset de sesión y estén disponibles en turnos futuros.

## Principio de diseño

La memoria episódica es una capa de persistencia semántica, no una base de datos relacional. El servicio extrae hechos de sesiones completadas y los hace recuperables por similitud. Los agentes sensei no acceden al grafo directamente — la integración ocurre via `PreloadMemory` (inyección automática al inicio del turno) y `LoadMemory` (búsqueda explícita).

## Rol en el sistema

```
turno completado  → after_agent_callback → episodic_memory.add_session_to_memory()
turno siguiente   → PreloadMemory        → episodic_memory.search_memory(query)
                                         → snippets episódicos inyectados en sensei
keeper (cron)     → episodic_memory API  → get observations by bonsai_slug
                                         → sintetiza → actualiza wiki
```

## Scope de memoria

- `user_id=telegram_id` — privacidad por usuario
- `agent_id=bonsai_slug` — permite al keeper filtrar por árbol sin mezclar usuarios

## Evolución prevista

El backend actual es Graphiti. FUTURE-007 evalúa una migración a mem0 (Postgres + pgvector) con un `CompositeMemoryService` que combine memoria episódica + búsqueda semántica en la wiki.
