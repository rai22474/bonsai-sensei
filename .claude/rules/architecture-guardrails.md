Antes de proponer o implementar cambios en un servicio:
- revisar `docs/architecture/decisions.md` para decisiones de arquitectura cross-service
- revisar `<service>/docs/vision.md` si la tarea afecta a flujos conversacionales o al diseño de agentes de ese servicio
- revisar `<service>/docs/issues.md` si hay errores raros o tests inestables en ese servicio
- revisar `<service>/docs/roadmap.md` antes de discutir nuevas features o priorizarlas; comprobar si ya existe una entrada FUTURE-XXX y usarla como punto de partida

Servicios: `bonsai_sensei/`, `knowledge_base/`, `episodic_memory/`

En conversaciones de producto (@product, "pensemos en", "siguiente feature", "qué hacemos con"):
- leer el `vision.md` del servicio afectado para conocer qué features están implementadas y cuáles pendientes
- leer el `roadmap.md` del servicio para no repetir análisis ya realizados
- referenciar el ID FUTURE-XXX correspondiente si existe

Al proponer un cambio:
- indicar qué decisión de arquitectura respeta o desafía
- advertir si toca una zona frágil o con incidencias conocidas

Evitar:
- reintroducir patrones ya descartados
- mover lógica a capas prohibidas
- "arreglos rápidos" que oculten deuda existente
