from bonsai_sensei.telegram.messages._formatting import format_date, display_name


def build_create_bonsai_confirmation(name: str, species_name: str) -> str:
    return f"¿Crear bonsái '{display_name(name)}' de especie '{display_name(species_name)}'?"


def build_delete_bonsai_confirmation(bonsai_id: int, bonsai_name: str) -> str:
    return f"¿Eliminar bonsái '{display_name(bonsai_name)}' (id={bonsai_id})? Esta acción es permanente."


def build_update_bonsai_confirmation(bonsai_id: int, bonsai_name: str, bonsai_data: dict) -> str:
    fields = ", ".join(f"{key}='{value}'" for key, value in bonsai_data.items())
    return f"¿Actualizar bonsái '{display_name(bonsai_name)}' (id={bonsai_id})? Cambios: {fields}"


def build_apply_fertilizer_confirmation(bonsai_name: str, fertilizer_name: str, amount: str) -> str:
    detail = f"'{display_name(fertilizer_name)}'" + (f" ({amount})" if amount else "")
    return f"¿Registrar aplicación de fertilizante {detail} en '{display_name(bonsai_name)}'?"


def build_apply_phytosanitary_confirmation(bonsai_name: str, phytosanitary_name: str, amount: str) -> str:
    detail = f"'{display_name(phytosanitary_name)}'" + (f" ({amount})" if amount else "")
    return f"¿Registrar tratamiento fitosanitario {detail} en '{display_name(bonsai_name)}'?"


def build_record_transplant_confirmation(bonsai_name: str, pot_size: str, pot_type: str, substrate: str) -> str:
    parts = [value for value in [pot_size, pot_type, substrate] if value]
    detail = f" ({', '.join(parts)})" if parts else ""
    return f"¿Registrar trasplante de '{display_name(bonsai_name)}'{detail}?"


_WORK_TYPE_LABELS = {
    "fertilizer_application": "Fertilización",
    "phytosanitary_application": "Fitosanitario",
    "transplant": "Trasplante",
}


def build_execute_planned_work_confirmation(work, bonsai_name: str) -> str:
    date_str = format_date(work.scheduled_date)
    type_label = _WORK_TYPE_LABELS.get(work.work_type, work.work_type)
    return f"¿Ejecutar '{type_label}' del {date_str} para '{display_name(bonsai_name)}'?"


def build_execute_planned_work_selection_question(bonsai_name: str) -> str:
    return f"¿Qué trabajo planificado de '{display_name(bonsai_name)}' deseas ejecutar?"


def build_execute_planned_work_option_label(work) -> str:
    type_label = _WORK_TYPE_LABELS.get(work.work_type, work.work_type)
    product_name = work.payload.get("fertilizer_name") or work.payload.get("phytosanitary_name") or ""
    if product_name:
        return f"{type_label} ({display_name(product_name)}) – {format_date(work.scheduled_date)}"
    return f"{type_label} – {format_date(work.scheduled_date)}"


def build_create_bonsai_species_selection_question() -> str:
    return "¿Qué especie quieres asignar al bonsái?"


def build_add_bonsai_photo_selection_question() -> str:
    return "¿A qué bonsái pertenece esta foto?"


def build_add_bonsai_photo_confirmation(bonsai_name: str) -> str:
    return f"¿Registrar esta foto para el bonsái '{display_name(bonsai_name)}'?"


def build_delete_bonsai_photo_selection_question(bonsai_name: str) -> str:
    return f"¿Qué foto de '{display_name(bonsai_name)}' deseas eliminar?"


def build_delete_bonsai_photo_option_label(taken_on) -> str:
    return f"Foto del {taken_on}"


def build_delete_bonsai_photo_confirmation(bonsai_name: str, taken_on: str) -> str:
    return f"¿Eliminar la foto del {format_date(taken_on)} del bonsái '{display_name(bonsai_name)}'? Esta acción es permanente."


def build_create_pest_event_confirmation(bonsai_name: str, pest_name: str) -> str:
    return f"¿Registrar detección de '{display_name(pest_name)}' en '{display_name(bonsai_name)}'?"


def build_applied_treatment_question(bonsai_name: str, pest_name: str) -> str:
    return (
        f"Se ha registrado la detección de '{display_name(pest_name)}' en '{display_name(bonsai_name)}'. "
        f"¿Has aplicado algún tratamiento fitosanitario?"
    )


def build_treatment_selection_question() -> str:
    return "¿Qué producto fitosanitario has aplicado?"


def build_phytosanitary_plan_review_proposal(bonsai_name: str, pest_name: str) -> str:
    return (
        f"Se ha detectado '{display_name(pest_name)}' en '{display_name(bonsai_name)}'. "
        f"Hay un plan fitosanitario activo que podría necesitar revisión. "
        f"¿Deseas revisar el plan?"
    )
