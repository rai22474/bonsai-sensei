from hamcrest import assert_that, equal_to

from bonsai_sensei.telegram.messages.garden_messages import (
    build_create_bonsai_confirmation,
    build_apply_fertilizer_confirmation,
    build_apply_phytosanitary_confirmation,
    build_delete_bonsai_confirmation,
)
from bonsai_sensei.telegram.messages.storekeeper_messages import (
    build_create_fertilizer_confirmation,
    build_create_phytosanitary_confirmation,
)
from bonsai_sensei.telegram.messages.botanist_messages import (
    build_create_species_confirmation,
    build_delete_species_confirmation,
)
from bonsai_sensei.telegram.messages.planning_messages import (
    build_fertilizer_confirmation,
    build_phytosanitary_confirmation,
)


def should_capitalize_bonsai_name_in_create_confirmation():
    result = build_create_bonsai_confirmation(name="naruto", species_name="elm")

    assert_that(result, equal_to("¿Crear bonsái 'Naruto' de especie 'Elm'?"),
        "Bonsai and species names must be capitalized in create confirmation")


def should_capitalize_bonsai_name_in_delete_confirmation():
    result = build_delete_bonsai_confirmation(bonsai_id=1, bonsai_name="naruto")

    assert_that(result, equal_to("¿Eliminar bonsái 'Naruto' (id=1)? Esta acción es permanente."),
        "Bonsai name must be capitalized in delete confirmation")


def should_capitalize_names_in_apply_fertilizer_confirmation():
    result = build_apply_fertilizer_confirmation(bonsai_name="naruto", fertilizer_name="biogold", amount="5ml")

    assert_that(result, equal_to("¿Registrar aplicación de fertilizante 'Biogold' (5ml) en 'Naruto'?"),
        "Bonsai and fertilizer names must be capitalized in apply fertilizer confirmation")


def should_capitalize_names_in_apply_phytosanitary_confirmation():
    result = build_apply_phytosanitary_confirmation(bonsai_name="shiro", phytosanitary_name="neem oil", amount="")

    assert_that(result, equal_to("¿Registrar tratamiento fitosanitario 'Neem oil' en 'Shiro'?"),
        "Bonsai and phytosanitary names must be capitalized in apply phytosanitary confirmation")


def should_capitalize_fertilizer_name_in_create_confirmation():
    result = build_create_fertilizer_confirmation(name="greenboom")

    assert_that(result, equal_to("¿Crear fertilizante 'Greenboom' y generar su ficha wiki?"),
        "Fertilizer name must be capitalized in create confirmation")


def should_capitalize_phytosanitary_name_in_create_confirmation():
    result = build_create_phytosanitary_confirmation(name="neem oil")

    assert_that(result, equal_to("¿Crear producto fitosanitario 'Neem oil' y generar su ficha wiki?"),
        "Phytosanitary name must be capitalized in create confirmation")


def should_capitalize_species_name_in_create_confirmation():
    result = build_create_species_confirmation(common_name="elm", scientific_name="Ulmus minor")

    assert_that(result, equal_to("¿Crear especie 'Elm' (Ulmus minor)?"),
        "Species common name must be capitalized; scientific name must remain unchanged")


def should_capitalize_species_name_in_delete_confirmation():
    result = build_delete_species_confirmation(species_name="ficus")

    assert_that(result, equal_to("¿Eliminar especie 'Ficus'? Esta acción es permanente."),
        "Species name must be capitalized in delete confirmation")


def should_capitalize_names_in_planning_fertilizer_confirmation():
    result = build_fertilizer_confirmation(
        bonsai_name="naruto", fertilizer_name="biogold", amount="5ml", scheduled_date="2026-05-15"
    )

    assert_that(result, equal_to("¿Aplicar fertilizante 'Biogold' (5ml) a 'Naruto' el 15/05/2026?"),
        "Bonsai and fertilizer names must be capitalized in planning fertilizer confirmation")


def should_capitalize_names_in_planning_phytosanitary_confirmation():
    result = build_phytosanitary_confirmation(
        bonsai_name="shiro", phytosanitary_name="neem oil", amount="", scheduled_date="2026-05-15"
    )

    assert_that(result, equal_to("¿Aplicar tratamiento fitosanitario 'Neem oil' a 'Shiro' el 15/05/2026?"),
        "Bonsai and phytosanitary names must be capitalized in planning phytosanitary confirmation")
