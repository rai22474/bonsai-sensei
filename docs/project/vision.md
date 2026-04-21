# Visión del Sistema

El valor central del sistema es ayudar a los usuarios a tomar decisiones en el complejo dominio del cultivo de bonsáis. Las operaciones estructuradas (crear planes de cultivo, registrar tratamientos) son secundarias — existen para mantener una base de conocimiento que enriquece las conversaciones.

## Principio de diseño

Las decisiones arquitectónicas deben favorecer la flexibilidad conversacional frente al control de pipeline. Los pipelines de planificación estrictos (mitori/shokunin) están reservados para operaciones de comando que necesitan coordinación de agentes. Todo lo demás debe ser lo más libre posible.

Debe evitarse añadir estado `active_mode` o enrutamiento complejo para flujos conversacionales salvo que sea estrictamente necesario.

## Casos de uso principales no implementados aún

- **Flujo de conversación diagnóstica**: el usuario describe síntomas (hojas amarillas, crecimiento anómalo) y el sistema ayuda a identificar la causa mediante un diálogo multi-turno.
- **Generación de plan estándar por especie/diseño**: genera un calendario de cultivo adaptado a la especie, el estilo de entrenamiento y la época del año.

Ambos deben seguir el patrón de agente libre (ver ADR-002 en decisions.md), no el pipeline mitori/shokunin.
