from datetime import datetime


def _format_date(scheduled_date) -> str:
    if isinstance(scheduled_date, str):
        scheduled_date = datetime.strptime(scheduled_date, "%Y-%m-%d").date()
    return scheduled_date.strftime("%d/%m/%Y")


def build_fertilizer_confirmation(bonsai_name: str, fertilizer_name: str, amount: str, scheduled_date: str) -> str:
    date_str = _format_date(scheduled_date)
    detail = f"'{fertilizer_name}'" + (f" ({amount})" if amount else "")
    return f"¿Aplicar fertilizante {detail} a '{bonsai_name}' el {date_str}?"


def build_phytosanitary_confirmation(bonsai_name: str, phytosanitary_name: str, amount: str, scheduled_date: str) -> str:
    date_str = _format_date(scheduled_date)
    detail = f"'{phytosanitary_name}'" + (f" ({amount})" if amount else "")
    return f"¿Aplicar tratamiento fitosanitario {detail} a '{bonsai_name}' el {date_str}?"


def build_transplant_confirmation(bonsai_name: str, scheduled_date: str, pot_size: str, pot_type: str, substrate: str) -> str:
    date_str = _format_date(scheduled_date)
    parts = [value for value in [pot_size, pot_type, substrate] if value]
    detail = f" ({', '.join(parts)})" if parts else ""
    return f"¿Trasplantar '{bonsai_name}'{detail} el {date_str}?"


def _build_fertilizer_delete_detail(payload: dict) -> str:
    fertilizer_name = payload.get("fertilizer_name", "fertilizante desconocido")
    amount = payload.get("amount")
    detail = f"'{fertilizer_name}'" + (f" ({amount})" if amount else "")
    return f"¿Eliminar aplicación de fertilizante {detail} del {{date_str}}?"


def _build_phytosanitary_delete_detail(payload: dict) -> str:
    product_name = payload.get("phytosanitary_name", "producto desconocido")
    amount = payload.get("amount")
    detail = f"'{product_name}'" + (f" ({amount})" if amount else "")
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


def build_delete_confirmation(work) -> str:
    date_str = _format_date(work.scheduled_date)
    payload = work.payload or {}
    builder = _DELETE_MESSAGE_BUILDERS.get(work.work_type)
    if builder:
        return builder(payload).format(date_str=date_str)
    return f"¿Eliminar trabajo '{work.work_type}' del {date_str}?"
