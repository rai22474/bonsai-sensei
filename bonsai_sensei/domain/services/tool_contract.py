TOOL_CONTRACT = """- Llama directamente a la tool con los datos disponibles. Las tools gestionan internamente la confirmación.
- Cuando una herramienta devuelva status 'success' o 'cancelled', responde al usuario sin llamar a más herramientas.
- Cuando una herramienta devuelva status 'error', informa al usuario del motivo sin llamar a otras herramientas."""
