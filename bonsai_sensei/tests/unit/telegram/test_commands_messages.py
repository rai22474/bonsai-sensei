from datetime import date

from hamcrest import assert_that, contains_string, equal_to

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.planned_work import PlannedWork
from bonsai_sensei.domain.species import Species, SpeciesCategory
from bonsai_sensei.telegram.messages.commands_messages import (
    build_bonsai_history,
    build_bonsai_list,
    build_fertilizer_list,
    build_phytosanitary_list,
    build_planned_works_list,
    build_species_list,
    build_upcoming_works_list,
    build_weekend_works_list,
    build_pest_list,
    build_weather_message,
    build_create_bonsai_success,
    build_species_not_found_message,
)
from bonsai_sensei.domain.pest import Pest


# --- build_bonsai_list ---

def should_return_no_bonsais_message_when_list_is_empty():
    result = build_bonsai_list([], {})

    assert_that(result, equal_to("No tienes bonsáis registrados."), "Empty list must return no-bonsais message")


def should_capitalize_bonsai_name_in_list():
    bonsais = [Bonsai(id=1, name="naruto", species_id=1)]

    result = build_bonsai_list(bonsais, {1: "ficus"})

    assert_that(result, contains_string("Naruto"), "Bonsai name must be capitalized")


def should_show_species_name_for_bonsai():
    bonsais = [Bonsai(id=1, name="naruto", species_id=1)]

    result = build_bonsai_list(bonsais, {1: "ficus"})

    assert_that(result, contains_string("Ficus"), "Species name must appear capitalized")


def should_show_fallback_when_species_not_in_map():
    bonsais = [Bonsai(id=1, name="naruto", species_id=99)]

    result = build_bonsai_list(bonsais, {})

    assert_that(result, contains_string("Especie 99"), "Missing species must show fallback label")


# --- build_planned_works_list ---

def should_return_no_planned_works_message_when_list_is_empty():
    result = build_planned_works_list("naruto", [])

    assert_that(result, equal_to("No hay trabajos planificados para Naruto."), "Empty list must return no-works message")


def should_put_date_before_work_type():
    works = [PlannedWork(id=7, bonsai_id=1, work_type="transplant", payload={}, scheduled_date=date(2026, 7, 1))]

    result = build_planned_works_list("naruto", works)

    date_pos = result.index("01/07/2026")
    type_pos = result.index("Trasplante")
    assert_that(date_pos < type_pos, equal_to(True), "Date must appear before work type")


def should_translate_fertilizer_work_type_to_spanish():
    works = [PlannedWork(id=1, bonsai_id=1, work_type="fertilizer_application", payload={}, scheduled_date=date(2026, 7, 1))]

    result = build_planned_works_list("naruto", works)

    assert_that(result, contains_string("Fertilización"), "fertilizer_application must render as 'Fertilización'")


def should_format_planned_work_date():
    works = [PlannedWork(id=1, bonsai_id=1, work_type="transplant", payload={}, scheduled_date=date(2026, 7, 15))]

    result = build_planned_works_list("naruto", works)

    assert_that(result, contains_string("15/07/2026"), "Scheduled date must be formatted as dd/MM/yyyy")


def should_include_fertilizer_name_and_amount_in_planned_work():
    works = [PlannedWork(id=1, bonsai_id=1, work_type="fertilizer_application",
                         payload={"fertilizer_name": "biogold", "amount": "5ml"}, scheduled_date=date(2026, 7, 1))]

    result = build_planned_works_list("naruto", works)

    assert_that(result, contains_string("— Fertilización (Biogold, 5ml)"), "Fertilizer name and amount must appear in planned work detail")


def should_include_phytosanitary_name_and_amount_in_planned_work():
    works = [PlannedWork(id=1, bonsai_id=1, work_type="phytosanitary_application",
                         payload={"phytosanitary_name": "neem oil", "amount": "2ml"}, scheduled_date=date(2026, 7, 1))]

    result = build_planned_works_list("naruto", works)

    assert_that(result, contains_string("Fitosanitario (Neem oil, 2ml)"), "Phytosanitary name and amount must appear in planned work detail")


def should_include_pot_details_in_transplant_planned_work():
    works = [PlannedWork(id=1, bonsai_id=1, work_type="transplant",
                         payload={"pot_size": "20cm", "pot_type": "barro", "substrate": "akadama"}, scheduled_date=date(2026, 7, 1))]

    result = build_planned_works_list("naruto", works)

    assert_that(result, contains_string("Trasplante (20cm, barro, akadama)"), "Pot details must appear in transplant planned work")


# --- build_upcoming_works_list ---

def should_return_no_upcoming_works_message_when_list_is_empty():
    result = build_upcoming_works_list([], {})

    assert_that(result, equal_to("No hay trabajos planificados próximamente."), "Empty list must return no-upcoming-works message")


def should_include_bonsai_name_in_upcoming_works():
    works = [PlannedWork(id=1, bonsai_id=5, work_type="transplant", payload={}, scheduled_date=date(2026, 7, 1))]

    result = build_upcoming_works_list(works, {5: "shiro"})

    assert_that(result, contains_string("Shiro"), "Bonsai name must appear capitalized in upcoming works")


def should_show_fallback_when_bonsai_not_in_map():
    works = [PlannedWork(id=1, bonsai_id=99, work_type="transplant", payload={}, scheduled_date=date(2026, 7, 1))]

    result = build_upcoming_works_list(works, {})

    assert_that(result, contains_string("Bonsái 99"), "Missing bonsai must show fallback label")


# --- build_fertilizer_list ---

def should_return_no_fertilizers_message_when_list_is_empty():
    result = build_fertilizer_list([])

    assert_that(result, equal_to("No hay fertilizantes registrados."), "Empty list must return no-fertilizers message")


def should_show_fertilizer_name_with_amount():
    fertilizers = [Fertilizer(id=1, name="biogold", recommended_amount="5ml")]

    result = build_fertilizer_list(fertilizers)

    assert_that(result, contains_string("Biogold (5ml)"), "Fertilizer name and amount must appear together")


def should_show_fertilizer_name_without_amount_when_empty():
    fertilizers = [Fertilizer(id=1, name="biogold", recommended_amount="")]

    result = build_fertilizer_list(fertilizers)

    assert_that(result, contains_string("Biogold"), "Fertilizer name must appear even without amount")


def should_not_show_parentheses_when_fertilizer_has_no_amount():
    fertilizers = [Fertilizer(id=1, name="biogold", recommended_amount="")]

    result = build_fertilizer_list(fertilizers)

    assert_that(result, equal_to("🧪 <b>Fertilizantes</b>\n\n• Biogold"), "No parentheses when amount is empty")


# --- build_phytosanitary_list ---

def should_return_no_phytosanitary_message_when_list_is_empty():
    result = build_phytosanitary_list([])

    assert_that(result, equal_to("No hay productos fitosanitarios registrados."), "Empty list must return no-phytosanitary message")


def should_show_phytosanitary_name_with_amount():
    phytosanitaries = [Phytosanitary(id=1, name="neem oil", recommended_amount="2ml")]

    result = build_phytosanitary_list(phytosanitaries)

    assert_that(result, contains_string("Neem oil (2ml)"), "Phytosanitary name and amount must appear together")


# --- build_species_list ---

def should_return_no_species_message_when_list_is_empty():
    result = build_species_list([])

    assert_that(result, equal_to("No hay especies registradas."), "Empty list must return no-species message")


def should_show_species_with_emoji_and_scientific_name():
    species_list = [Species(id=1, name="elm", scientific_name="Ulmus minor", category=SpeciesCategory.deciduous)]

    result = build_species_list(species_list)

    assert_that(result, contains_string("Elm (Ulmus minor)"), "Species must show capitalized name and scientific name")


def should_show_species_without_scientific_name():
    species_list = [Species(id=1, name="ficus", category=SpeciesCategory.tropical)]

    result = build_species_list(species_list)

    assert_that(result, contains_string("Ficus"), "Species name must appear without parentheses when no scientific name")


def should_not_show_parentheses_when_species_has_no_scientific_name():
    species_list = [Species(id=1, name="ficus", category=SpeciesCategory.tropical)]

    result = build_species_list(species_list)

    assert_that(result, equal_to("🌿 <b>Especies</b>\n\n🌿 Ficus"), "No parentheses when scientific name is absent")


# --- build_bonsai_history ---

def should_return_no_history_message_when_events_is_empty():
    result = build_bonsai_history("naruto", [])

    assert_that(result, equal_to("No hay eventos registrados para Naruto."), "Empty list must return no-history message")


def should_list_most_recent_event_first():
    events = [
        {"event_type": "transplant", "payload": {}, "occurred_at": "2026-01-01T10:00:00+00:00"},
        {"event_type": "transplant", "payload": {}, "occurred_at": "2026-06-01T10:00:00+00:00"},
    ]

    result = build_bonsai_history("naruto", events)

    june_pos = result.index("01/06/2026")
    jan_pos = result.index("01/01/2026")
    assert_that(june_pos < jan_pos, equal_to(True), "Most recent event must appear before older event")


def should_format_fertilizer_event_with_product_and_amount():
    events = [
        {"event_type": "fertilizer_application", "payload": {"fertilizer_name": "biogold", "amount": "5ml"}, "occurred_at": "2026-05-01T10:00:00+00:00"},
    ]

    result = build_bonsai_history("naruto", events)

    assert_that(result, contains_string("Fertilización (Biogold, 5ml)"), "Fertilizer event must show product name and amount")


def should_format_transplant_event_with_pot_details():
    events = [
        {"event_type": "transplant", "payload": {"pot_size": "20cm", "pot_type": "barro"}, "occurred_at": "2026-05-01T10:00:00+00:00"},
    ]

    result = build_bonsai_history("naruto", events)

    assert_that(result, contains_string("Trasplante (20cm, barro)"), "Transplant event must show pot details")


def should_format_pest_detection_event_with_pest_name():
    events = [
        {"event_type": "pest_detection", "payload": {"pest_name": "araña roja"}, "occurred_at": "2026-05-01T10:00:00+00:00"},
    ]

    result = build_bonsai_history("naruto", events)

    assert_that(result, contains_string("Plaga detectada: Araña roja"), "Pest detection event must show pest name")


def should_limit_history_to_last_twenty_events():
    events = [
        {"event_type": "transplant", "payload": {}, "occurred_at": f"2026-0{(i // 28) + 1}-{(i % 28) + 1:02d}T10:00:00+00:00"}
        for i in range(25)
    ]

    result = build_bonsai_history("naruto", events)

    assert_that(result, contains_string("últimos 20"), "History must be limited to last 20 events")


# --- build_weekend_works_list ---

def should_return_no_weekend_works_message_when_list_is_empty():
    saturday = date(2026, 6, 6)
    sunday = date(2026, 6, 7)

    result = build_weekend_works_list(saturday, sunday, [], {})

    assert_that(result, contains_string("No hay trabajos"), "Empty weekend must show no-works message")


def should_include_date_range_in_weekend_header():
    saturday = date(2026, 6, 6)
    sunday = date(2026, 6, 7)

    result = build_weekend_works_list(saturday, sunday, [], {})

    assert_that(result, contains_string("06/06/2026"), "Saturday date must appear in header")


def should_show_bonsai_name_and_work_type_in_weekend_list():
    saturday = date(2026, 6, 6)
    sunday = date(2026, 6, 7)
    works = [PlannedWork(id=1, bonsai_id=3, work_type="transplant", payload={}, scheduled_date=saturday)]

    result = build_weekend_works_list(saturday, sunday, works, {3: "shiro"})

    assert_that(result, contains_string("Shiro"), "Bonsai name must appear in weekend list")


def should_include_fertilizer_detail_in_weekend_list():
    saturday = date(2026, 6, 6)
    sunday = date(2026, 6, 7)
    works = [PlannedWork(id=1, bonsai_id=1, work_type="fertilizer_application",
                         payload={"fertilizer_name": "biogold", "amount": "5ml"}, scheduled_date=saturday)]

    result = build_weekend_works_list(saturday, sunday, works, {1: "naruto"})

    assert_that(result, contains_string("Biogold, 5ml"), "Fertilizer detail must appear in weekend list")


# --- build_pest_list ---

def should_return_no_pests_message_when_list_is_empty():
    result = build_pest_list([])

    assert_that(result, equal_to("No hay plagas registradas."), "Empty list must return no-pests message")


def should_capitalize_pest_name_in_list():
    pests = [Pest(id=1, name="araña roja")]

    result = build_pest_list(pests)

    assert_that(result, contains_string("Araña roja"), "Pest name must be capitalized")


# --- build_weather_message ---

def should_show_location_and_temperature_in_weather_message():
    weather_result = {
        "status": "success",
        "result": {
            "location": "Madrid",
            "current": {"description": "Sunny", "temperature_c": "22"},
            "min_temp_c": "15",
            "max_temp_c": "25",
            "max_frost_chance": 0,
            "hourly": "",
            "summary": "",
        },
    }

    result = build_weather_message(weather_result)

    assert_that(result, contains_string("Madrid"), "Location must appear in weather message")


def should_show_frost_warning_when_frost_risk_high():
    weather_result = {
        "status": "success",
        "result": {
            "location": "Madrid",
            "current": {"description": "Clear", "temperature_c": "1"},
            "min_temp_c": "-2",
            "max_temp_c": "5",
            "max_frost_chance": 80,
            "hourly": "",
            "summary": "",
        },
    }

    result = build_weather_message(weather_result)

    assert_that(result, contains_string("⚠️"), "Frost warning emoji must appear when frost risk > 50%")


def should_return_error_message_when_weather_fetch_fails():
    weather_result = {"status": "error", "message": "Could not fetch weather for XYZ."}

    result = build_weather_message(weather_result)

    assert_that(result, contains_string("No se pudo obtener"), "Error status must produce error message")


# --- build_create_bonsai_success / build_species_not_found_message ---

def should_show_bonsai_and_species_name_in_create_success():
    result = build_create_bonsai_success("naruto", "ficus")

    assert_that(result, contains_string("Naruto"), "Bonsai name must appear capitalized in success message")


def should_show_species_name_in_not_found_message():
    result = build_species_not_found_message("ficus")

    assert_that(result, contains_string("ficus"), "Species name must appear in not-found message")
