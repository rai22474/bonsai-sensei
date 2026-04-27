from bonsai_sensei.telegram.messages._formatting import format_date


def build_create_bonsai_confirmation(name: str, species_name: str) -> str:
    return f"¿Crear bonsái '{name}' de especie '{species_name}'?"


def build_delete_bonsai_confirmation(bonsai_id: int, bonsai_name: str) -> str:
    return f"¿Eliminar bonsái '{bonsai_name}' (id={bonsai_id})? Esta acción es permanente."


def build_update_bonsai_confirmation(bonsai_id: int, bonsai_name: str, bonsai_data: dict) -> str:
    fields = ", ".join(f"{key}='{value}'" for key, value in bonsai_data.items())
    return f"¿Actualizar bonsái '{bonsai_name}' (id={bonsai_id})? Cambios: {fields}"


def build_apply_fertilizer_confirmation(bonsai_name: str, fertilizer_name: str, amount: str) -> str:
    detail = f"'{fertilizer_name}'" + (f" ({amount})" if amount else "")
    return f"¿Registrar aplicación de fertilizante {detail} en '{bonsai_name}'?"


def build_apply_phytosanitary_confirmation(bonsai_name: str, phytosanitary_name: str, amount: str) -> str:
    detail = f"'{phytosanitary_name}'" + (f" ({amount})" if amount else "")
    return f"¿Registrar tratamiento fitosanitario {detail} en '{bonsai_name}'?"


def build_record_transplant_confirmation(bonsai_name: str, pot_size: str, pot_type: str, substrate: str) -> str:
    parts = [value for value in [pot_size, pot_type, substrate] if value]
    detail = f" ({', '.join(parts)})" if parts else ""
    return f"¿Registrar trasplante de '{bonsai_name}'{detail}?"


def build_execute_planned_work_confirmation(work) -> str:
    date_str = format_date(work.scheduled_date)
    return f"¿Ejecutar trabajo planificado '{work.work_type}' del {date_str} para el bonsái {work.bonsai_id}?"


def build_add_bonsai_photo_selection_question() -> str:
    return "¿A qué bonsái pertenece esta foto?"


def build_add_bonsai_photo_confirmation(bonsai_name: str) -> str:
    return f"¿Registrar esta foto para el bonsái '{bonsai_name}'?"


def build_delete_bonsai_photo_selection_question(bonsai_name: str) -> str:
    return f"¿Qué foto de '{bonsai_name}' deseas eliminar?"


def build_delete_bonsai_photo_confirmation(bonsai_name: str, taken_on: str) -> str:
    return f"¿Eliminar la foto del {format_date(taken_on)} del bonsái '{bonsai_name}'? Esta acción es permanente."
