from bonsai_sensei.telegram.messages._formatting import format_date, display_name


def build_fertilization_type_question() -> str:
    return "¿Qué tipo de fertilización quieres planificar?"


def build_fertilization_type_options() -> list[str]:
    return ["Fertilización puntual", "Plan de fertilización"]


def build_fertilizer_confirmation(bonsai_name: str, fertilizer_name: str, amount: str, scheduled_date: str) -> str:
    date_str = format_date(scheduled_date)
    detail = f"'{display_name(fertilizer_name)}'" + (f" ({amount})" if amount else "")
    return f"¿Aplicar fertilizante {detail} a '{display_name(bonsai_name)}' el {date_str}?"


def build_phytosanitary_confirmation(bonsai_name: str, phytosanitary_name: str, amount: str, scheduled_date: str) -> str:
    date_str = format_date(scheduled_date)
    detail = f"'{display_name(phytosanitary_name)}'" + (f" ({amount})" if amount else "")
    return f"¿Aplicar tratamiento fitosanitario {detail} a '{display_name(bonsai_name)}' el {date_str}?"


def build_transplant_confirmation(bonsai_name: str, scheduled_date: str, pot_size: str, pot_type: str, substrate: str) -> str:
    date_str = format_date(scheduled_date)
    parts = [value for value in [pot_size, pot_type, substrate] if value]
    detail = f" ({', '.join(parts)})" if parts else ""
    return f"¿Trasplantar '{display_name(bonsai_name)}'{detail} el {date_str}?"


def _build_fertilizer_delete_detail(payload: dict) -> str:
    fertilizer_name = payload.get("fertilizer_name", "fertilizante desconocido")
    amount = payload.get("amount")
    detail = f"'{display_name(fertilizer_name)}'" + (f" ({amount})" if amount else "")
    return f"¿Eliminar aplicación de fertilizante {detail} del {{date_str}}?"


def _build_phytosanitary_delete_detail(payload: dict) -> str:
    product_name = payload.get("phytosanitary_name", "producto desconocido")
    amount = payload.get("amount")
    detail = f"'{display_name(product_name)}'" + (f" ({amount})" if amount else "")
    return f"¿Eliminar aplicación fitosanitaria {detail} del {{date_str}}?"


def _build_transplant_delete_detail(payload: dict) -> str:
    parts = [value for key in ("pot_size", "pot_type", "substrate") if (value := payload.get(key))]
    detail = f" ({', '.join(parts)})" if parts else ""
    return f"¿Eliminar trasplante{detail} del {{date_str}}?"


_DELETE_MESSAGE_BUILDERS = {
    "fertilizer_application": _build_fertilizer_delete_detail,
    "phytosanitary_application": _build_phytosanitary_delete_detail,
    "transplant": _build_transplant_delete_detail,
}


def build_fertilization_plan_confirmation(bonsai_name: str, period_start: str, period_end: str, entry_count: int) -> str:
    return f"¿Crear plan de fertilización para '{display_name(bonsai_name)}' del {format_date(period_start)} al {format_date(period_end)} con {entry_count} aplicaciones?"


def build_abandon_plan_confirmation(bonsai_name: str, period_start: str, period_end: str, reason: str) -> str:
    return f"¿Abandonar el plan de fertilización de '{display_name(bonsai_name)}' ({format_date(period_start)} → {format_date(period_end)})?\nMotivo: {reason}"


def build_abandon_phytosanitary_plan_confirmation(bonsai_name: str, period_start: str, period_end: str, reason: str) -> str:
    return f"¿Abandonar el plan fitosanitario de '{display_name(bonsai_name)}' ({format_date(period_start)} → {format_date(period_end)})?\nMotivo: {reason}"


def build_delete_confirmation(work) -> str:
    date_str = format_date(work.scheduled_date)
    payload = work.payload or {}
    builder = _DELETE_MESSAGE_BUILDERS.get(work.work_type)
    if builder:
        return builder(payload).format(date_str=date_str)
    return f"¿Eliminar trabajo '{work.work_type}' del {date_str}?"
