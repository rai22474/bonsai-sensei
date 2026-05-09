Antes de proponer o implementar cambios:
- revisar `docs/architecture/decisions.md`
- revisar `docs/project/vision.md` si la tarea afecta a flujos conversacionales o al diseño de agentes
- revisar `docs/project/technical-debt.md` si la tarea toca módulos existentes
- revisar `docs/project/known-issues.md` si hay errores raros o tests inestables
- revisar `docs/project/future-work.md` antes de discutir nuevas features o priorizarlas; comprobar si ya existe una entrada FUTURE-XXX y usarla como punto de partida

En conversaciones de producto (@product, "pensemos en", "siguiente feature", "qué hacemos con"):
- leer `docs/project/vision.md` para conocer qué features están implementadas y cuáles pendientes
- leer `docs/project/future-work.md` para no repetir análisis ya realizados
- referenciar el ID FUTURE-XXX correspondiente si existe

Al proponer un cambio:
- indicar qué decisión de arquitectura respeta o desafía
- indicar si aumenta, mantiene o reduce deuda técnica
- advertir si toca una zona frágil o con incidencias conocidas

Evitar:
- reintroducir patrones ya descartados
- mover lógica a capas prohibidas
- "arreglos rápidos" que oculten deuda existente
