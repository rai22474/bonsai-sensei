def build_create_species_selection_question(common_name: str) -> str:
    return f"Se encontraron varios nombres científicos para '{common_name}'. ¿Cuál es el correcto?"


def build_create_species_confirmation(common_name: str, scientific_name: str) -> str:
    return f"¿Crear especie '{common_name}' ({scientific_name})?"


def build_delete_species_confirmation(species_name: str) -> str:
    return f"¿Eliminar especie '{species_name}'? Esta acción es permanente."


def build_update_species_confirmation(species_name: str, species_data: dict) -> str:
    fields = ", ".join(f"{key}='{value}'" for key, value in species_data.items())
    return f"¿Actualizar especie '{species_name}'? Cambios: {fields}"


def build_refresh_species_wiki_confirmation(name: str) -> str:
    return f"¿Regenerar la ficha wiki de '{name}' con información actualizada de internet?"
