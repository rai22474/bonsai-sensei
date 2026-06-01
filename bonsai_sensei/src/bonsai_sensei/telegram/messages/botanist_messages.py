from bonsai_sensei.telegram.messages._formatting import display_name


def build_create_species_selection_question(common_name: str) -> str:
    return f"Se encontraron varios nombres científicos para '{display_name(common_name)}'. ¿Cuál es el correcto?"


def build_create_species_confirmation(common_name: str, scientific_name: str) -> str:
    return f"¿Crear especie '{display_name(common_name)}' ({scientific_name})?"


def build_delete_species_confirmation(species_name: str) -> str:
    return f"¿Eliminar especie '{display_name(species_name)}'? Esta acción es permanente."


def build_update_species_confirmation(species_name: str, species_data: dict) -> str:
    fields = ", ".join(f"{key}='{value}'" for key, value in species_data.items())
    return f"¿Actualizar especie '{display_name(species_name)}'? Cambios: {fields}"


def build_refresh_species_wiki_confirmation(name: str) -> str:
    return f"¿Regenerar la ficha wiki de '{display_name(name)}' con información actualizada de internet?"


def build_create_pest_confirmation(name: str) -> str:
    return f"¿Registrar plaga '{display_name(name)}' en el catálogo y generar su ficha wiki?"


def build_delete_pest_confirmation(name: str) -> str:
    return f"¿Eliminar plaga '{display_name(name)}' del catálogo? Esta acción es permanente."
