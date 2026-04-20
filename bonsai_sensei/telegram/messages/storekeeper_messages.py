def build_create_fertilizer_confirmation(name: str, usage_sheet: str, recommended_amount: str) -> str:
    amount_detail = f" (dosis: {recommended_amount.strip()})" if recommended_amount and recommended_amount.strip() else ""
    return f"¿Crear fertilizante '{name}'{amount_detail}?"


def build_delete_fertilizer_confirmation(name: str) -> str:
    return f"¿Eliminar fertilizante '{name}'? Esta acción es permanente."


def build_update_fertilizer_confirmation(name: str, fertilizer_data: dict) -> str:
    fields = [key for key, value in fertilizer_data.items() if value is not None]
    return f"¿Actualizar fertilizante '{name}'? Campos: {', '.join(fields)}"


def build_create_phytosanitary_confirmation(name: str, usage_sheet: str, recommended_amount: str) -> str:
    amount_detail = f" (dosis: {recommended_amount.strip()})" if recommended_amount and recommended_amount.strip() else ""
    return f"¿Crear producto fitosanitario '{name}'{amount_detail}?"


def build_delete_phytosanitary_confirmation(name: str) -> str:
    return f"¿Eliminar producto fitosanitario '{name}'? Esta acción es permanente."


def build_update_phytosanitary_confirmation(name: str, phytosanitary_data: dict) -> str:
    fields = [key for key, value in phytosanitary_data.items() if value is not None]
    return f"¿Actualizar producto fitosanitario '{name}'? Campos: {', '.join(fields)}"
