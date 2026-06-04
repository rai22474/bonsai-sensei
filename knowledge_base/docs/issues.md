# Issues Conocidos

## ISSUE-KB-001 — MCP `search_wiki_knowledge` devuelve siempre vacío

**Síntoma:** Llamadas a `search_wiki_knowledge` vía MCP server devuelven `{"results": []}` independientemente de la query.

**Causa raíz:** `main.py` crea el MCP server (`create_mcp_server()`) sin pasar `embed_func` ni `search_index`. El tool handler cae en el fallback `result = {"results": []}` en lugar de ejecutar la búsqueda semántica.

**Workaround:** Usar la API REST directamente: `POST /api/wiki/index/search`. El agente sensei usa el HTTP client (`wiki_client.py`) que sí funciona.

**Objetivo:** Pasar `embed_func` y `search_index` al MCP server en `main.py` igual que se hace para el HTTP endpoint.

**Relacionado:** `knowledge_base/src/knowledge_base/mcp/wiki_server.py:100-113`, `knowledge_base/src/knowledge_base/main.py`.
