Antes de proponer o implementar cambios:
- revisar `docs/architecture/decisions.md`
- revisar `docs/project/vision.md` si la tarea afecta a flujos conversacionales o al diseño de agentes
- revisar `docs/project/technical-debt.md` si la tarea toca módulos existentes
- revisar `docs/project/known-issues.md` si hay errores raros o tests inestables

Al proponer un cambio:
- indicar qué decisión de arquitectura respeta o desafía
- indicar si aumenta, mantiene o reduce deuda técnica
- advertir si toca una zona frágil o con incidencias conocidas

Evitar:
- reintroducir patrones ya descartados
- mover lógica a capas prohibidas
- "arreglos rápidos" que oculten deuda existente
