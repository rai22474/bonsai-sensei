def build_create_fertilizer_confirmation(name: str) -> str:
    return f"¿Crear fertilizante '{name}' y generar su ficha wiki?"


def build_delete_fertilizer_confirmation(name: str) -> str:
    return f"¿Eliminar fertilizante '{name}'? Esta acción es permanente."


def build_update_fertilizer_confirmation(name: str, recommended_amount: str) -> str:
    return f"¿Actualizar la cantidad recomendada del fertilizante '{name}' a '{recommended_amount}'?"


def build_create_phytosanitary_confirmation(name: str) -> str:
    return f"¿Crear producto fitosanitario '{name}' y generar su ficha wiki?"


def build_delete_phytosanitary_confirmation(name: str) -> str:
    return f"¿Eliminar producto fitosanitario '{name}'? Esta acción es permanente."


def build_update_phytosanitary_confirmation(name: str, recommended_amount: str) -> str:
    return f"¿Actualizar la cantidad recomendada del producto fitosanitario '{name}' a '{recommended_amount}'?"


def build_refresh_fertilizer_wiki_confirmation(name: str) -> str:
    return f"¿Regenerar la ficha wiki del fertilizante '{name}' con información actualizada de internet?"


def build_refresh_phytosanitary_wiki_confirmation(name: str) -> str:
    return f"¿Regenerar la ficha wiki del producto fitosanitario '{name}' con información actualizada de internet?"
