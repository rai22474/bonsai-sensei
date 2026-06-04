from datetime import date, datetime

from bonsai_sensei.telegram.messages._formatting import display_name, format_date

_WORK_TYPE_LABELS = {
    "fertilizer_application": "Fertilización",
    "phytosanitary_application": "Fitosanitario",
    "transplant": "Trasplante",
}

_EVENT_TYPE_LABELS = {
    "fertilizer_application": "Fertilización",
    "phytosanitary_application": "Fitosanitario",
    "transplant": "Trasplante",
    "pest_detection": "Plaga detectada",
}

_HISTORY_LIMIT = 20


def build_bonsai_list(bonsais: list, species_id_to_name: dict) -> str:
    if not bonsais:
        return "No tienes bonsáis registrados."
    lines = ["🪴 <b>Mis bonsáis</b>\n"]
    for bonsai in bonsais:
        species_name = display_name(species_id_to_name.get(bonsai.species_id, f"Especie {bonsai.species_id}"))
        lines.append(f"• {display_name(bonsai.name)} ({species_name})")
    return "\n".join(lines)


def build_planned_works_list(bonsai_name: str, works: list) -> str:
    if not works:
        return f"No hay trabajos planificados para {display_name(bonsai_name)}."
    lines = [f"📅 <b>Plan de {display_name(bonsai_name)}</b>\n"]
    for work in works:
        type_label = _WORK_TYPE_LABELS.get(work.work_type, work.work_type)
        detail = _format_work_detail(work.work_type, work.payload or {})
        suffix = f" ({detail})" if detail else ""
        lines.append(f"• {format_date(work.scheduled_date)} — {type_label}{suffix}")
    return "\n".join(lines)


def _format_work_detail(work_type: str, payload: dict) -> str:
    if work_type == "fertilizer_application":
        name = display_name(payload.get("fertilizer_name", ""))
        amount = payload.get("amount", "")
        if name and amount:
            return f"{name}, {amount}"
        return name
    if work_type == "phytosanitary_application":
        name = display_name(payload.get("phytosanitary_name", ""))
        amount = payload.get("amount", "")
        if name and amount:
            return f"{name}, {amount}"
        return name
    if work_type == "transplant":
        parts = [payload.get(key) for key in ("pot_size", "pot_type", "substrate") if payload.get(key)]
        return ", ".join(parts)
    return ""


def build_upcoming_works_list(works: list, bonsai_id_to_name: dict) -> str:
    if not works:
        return "No hay trabajos planificados próximamente."
    lines = ["📅 <b>Próximos trabajos</b>\n"]
    for work in works:
        bonsai_name = display_name(bonsai_id_to_name.get(work.bonsai_id, f"Bonsái {work.bonsai_id}"))
        type_label = _WORK_TYPE_LABELS.get(work.work_type, work.work_type)
        lines.append(f"• {format_date(work.scheduled_date)} — {bonsai_name}: {type_label}")
    return "\n".join(lines)


def build_fertilizer_list(fertilizers: list) -> str:
    if not fertilizers:
        return "No hay fertilizantes registrados."
    lines = ["🧪 <b>Fertilizantes</b>\n"]
    for fertilizer in fertilizers:
        amount = f" ({fertilizer.recommended_amount})" if fertilizer.recommended_amount else ""
        lines.append(f"• {display_name(fertilizer.name)}{amount}")
    return "\n".join(lines)


def build_phytosanitary_list(phytosanitaries: list) -> str:
    if not phytosanitaries:
        return "No hay productos fitosanitarios registrados."
    lines = ["🛡️ <b>Fitosanitarios</b>\n"]
    for product in phytosanitaries:
        amount = f" ({product.recommended_amount})" if product.recommended_amount else ""
        lines.append(f"• {display_name(product.name)}{amount}")
    return "\n".join(lines)


def build_species_list(species_list: list) -> str:
    if not species_list:
        return "No hay especies registradas."
    lines = ["🌿 <b>Especies</b>\n"]
    for species in species_list:
        scientific = f" ({species.scientific_name})" if species.scientific_name else ""
        lines.append(f"{species.get_emoji()} {display_name(species.name)}{scientific}")
    return "\n".join(lines)


def build_bonsai_history(bonsai_name: str, events: list) -> str:
    if not events:
        return f"No hay eventos registrados para {display_name(bonsai_name)}."
    recent = events[-_HISTORY_LIMIT:]
    lines = [f"📖 <b>Historial de {display_name(bonsai_name)}</b> (últimos {len(recent)})\n"]
    for event in reversed(recent):
        date_str = _format_event_date(event["occurred_at"])
        type_label = _format_event_label(event["event_type"], event.get("payload", {}))
        lines.append(f"• {date_str} — {type_label}")
    return "\n".join(lines)


def _format_event_date(occurred_at: str) -> str:
    return datetime.fromisoformat(occurred_at).strftime("%d/%m/%Y")


def _format_event_label(event_type: str, payload: dict) -> str:
    base = _EVENT_TYPE_LABELS.get(event_type, event_type)
    if event_type == "fertilizer_application":
        name = payload.get("fertilizer_name", "")
        amount = payload.get("amount", "")
        detail = display_name(name) if name else ""
        if detail and amount:
            return f"{base} ({detail}, {amount})"
        if detail:
            return f"{base} ({detail})"
    elif event_type == "phytosanitary_application":
        name = payload.get("phytosanitary_name", "")
        amount = payload.get("amount", "")
        detail = display_name(name) if name else ""
        if detail and amount:
            return f"{base} ({detail}, {amount})"
        if detail:
            return f"{base} ({detail})"
    elif event_type == "pest_detection":
        name = payload.get("pest_name", "")
        if name:
            return f"{base}: {display_name(name)}"
    elif event_type == "transplant":
        parts = [payload.get(key) for key in ("pot_size", "pot_type", "substrate") if payload.get(key)]
        if parts:
            return f"{base} ({', '.join(parts)})"
    return base


def build_weekend_works_list(saturday: date, sunday: date, works: list, bonsai_id_to_name: dict) -> str:
    header = f"📅 <b>Fin de semana</b> ({format_date(saturday)} – {format_date(sunday)})\n"
    if not works:
        return header + "\nNo hay trabajos planificados para este fin de semana."
    lines = [header]
    for work in works:
        bonsai_name = display_name(bonsai_id_to_name.get(work.bonsai_id, f"Bonsái {work.bonsai_id}"))
        type_label = _WORK_TYPE_LABELS.get(work.work_type, work.work_type)
        detail = _format_work_detail(work.work_type, work.payload or {})
        suffix = f" ({detail})" if detail else ""
        lines.append(f"• {format_date(work.scheduled_date)} — {bonsai_name}: {type_label}{suffix}")
    return "\n".join(lines)


def build_pest_list(pests: list) -> str:
    if not pests:
        return "No hay plagas registradas."
    lines = ["🐛 <b>Plagas</b>\n"]
    for pest in pests:
        lines.append(f"• {display_name(pest.name)}")
    return "\n".join(lines)


def build_weather_message(weather_result: dict) -> str:
    if weather_result.get("status") != "success":
        return f"No se pudo obtener el tiempo: {weather_result.get('message', 'error desconocido')}."
    result = weather_result["result"]
    location = result["location"]
    desc = result["current"]["description"]
    temp = result["current"]["temperature_c"]
    min_temp = result["min_temp_c"]
    max_temp = result["max_temp_c"]
    frost = int(result["max_frost_chance"])
    frost_line = f"\n⚠️ <b>Riesgo de helada: {frost}%</b>" if frost > 50 else f"\nRiesgo de helada: {frost}%"
    return (
        f"🌤 <b>{location}</b>\n\n"
        f"Actual: {desc}, {temp}°C\n"
        f"Min/Max: {min_temp}°C / {max_temp}°C"
        f"{frost_line}"
    )


def build_no_location_message() -> str:
    return "No tienes ubicación registrada. Dile al sensei tu ciudad para guardarla."


def build_create_bonsai_success(bonsai_name: str, species_name: str) -> str:
    return f"✅ Bonsái '{display_name(bonsai_name)}' ({display_name(species_name)}) creado correctamente."


def build_species_not_found_message(species_name: str) -> str:
    return f"No encontré ninguna especie llamada '{species_name}'. Usa /especies para ver las disponibles."


def build_bonsai_not_found_message(bonsai_name: str) -> str:
    return f"No encontré ningún bonsái llamado '{bonsai_name}'."


def build_fertilizer_not_found_message(fertilizer_name: str) -> str:
    return f"No encontré ningún fertilizante llamado '{fertilizer_name}'. Usa /fertilizantes para ver el catálogo."


def build_phytosanitary_not_found_message(phytosanitary_name: str) -> str:
    return f"No encontré ningún fitosanitario llamado '{phytosanitary_name}'. Usa /fitosanitarios para ver el catálogo."


def build_pest_not_found_message(pest_name: str) -> str:
    return f"No encontré ninguna plaga llamada '{pest_name}'. Usa /plagas para ver el catálogo."


def build_no_planned_works_message(bonsai_name: str) -> str:
    return f"No hay trabajos planificados para {display_name(bonsai_name)}."


def build_apply_fertilizer_success(bonsai_name: str, fertilizer_name: str) -> str:
    return f"✅ Fertilización con {display_name(fertilizer_name)} registrada en {display_name(bonsai_name)}."


def build_apply_phytosanitary_success(bonsai_name: str, phytosanitary_name: str) -> str:
    return f"✅ Tratamiento con {display_name(phytosanitary_name)} registrado en {display_name(bonsai_name)}."


def build_create_pest_event_success(bonsai_name: str, pest_name: str) -> str:
    return f"✅ Detección de {display_name(pest_name)} registrada en {display_name(bonsai_name)}."


def build_record_transplant_success(bonsai_name: str) -> str:
    return f"✅ Trasplante registrado para {display_name(bonsai_name)}."


def build_execute_planned_work_success(bonsai_name: str, work_type: str) -> str:
    label = _WORK_TYPE_LABELS.get(work_type, work_type)
    return f"✅ {label} ejecutada para {display_name(bonsai_name)}."


def build_fertilizer_already_exists_message(name: str) -> str:
    return f"El fertilizante '{display_name(name)}' ya existe en el catálogo."


def build_phytosanitary_already_exists_message(name: str) -> str:
    return f"El fitosanitario '{display_name(name)}' ya existe en el catálogo."


def build_species_already_exists_message(name: str) -> str:
    return f"La especie '{display_name(name)}' ya está registrada."


def build_scientific_name_not_found_message(common_name: str) -> str:
    return f"No encontré nombre científico para '{common_name}'. Prueba con /nueva_especie <nombre> <nombre_científico>."


def build_create_fertilizer_success(name: str) -> str:
    return f"✅ Fertilizante '{display_name(name)}' creado con ficha wiki generada."


def build_create_phytosanitary_success(name: str) -> str:
    return f"✅ Fitosanitario '{display_name(name)}' creado con ficha wiki generada."


def build_create_species_success(common_name: str, scientific_name: str) -> str:
    return f"✅ Especie '{display_name(common_name)}' ({scientific_name}) creada con guía de cultivo generada."
