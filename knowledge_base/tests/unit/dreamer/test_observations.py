import pytest
from unittest.mock import AsyncMock, MagicMock
from hamcrest import assert_that, equal_to, none, contains_string

from knowledge_base.dreamer.observations import _build_observation_path, execute_integrate_observations


def should_build_bonsai_path():
    path = _build_observation_path("bonsai", "Tanaka", "user123")
    assert_that(path, equal_to("users/user123/bonsai/tanaka/index.md"))


def should_build_species_notes_path_for_user():
    path = _build_observation_path("species", "Juniperus chinensis", "user123")
    assert_that(path, equal_to("users/user123/species-notes/juniperus-chinensis.md"))


def should_build_techniques_notes_path_for_user():
    path = _build_observation_path("techniques", "Alambrado", "user123")
    assert_that(path, equal_to("users/user123/techniques-notes/alambrado.md"))


def should_build_profile_path_without_entity():
    path = _build_observation_path("profile", "preferences", "user123")
    assert_that(path, equal_to("users/user123/profile/preferences.md"))


def should_build_global_species_path_for_admin_correction():
    path = _build_observation_path("species", "Ficus retusa", None)
    assert_that(path, equal_to("species/ficus-retusa.md"))


def should_build_global_techniques_path_for_admin_correction():
    path = _build_observation_path("techniques", "Poda de mantenimiento", None)
    assert_that(path, equal_to("techniques/poda-de-mantenimiento.md"))


def should_return_none_for_ignore():
    path = _build_observation_path("ignore", "", None)
    assert_that(path, none())


def should_return_none_for_unknown_type():
    path = _build_observation_path("unknown-type", "something", "user123")
    assert_that(path, none())


def should_return_none_for_bonsai_without_user_id():
    path = _build_observation_path("bonsai", "Tanaka", None)
    assert_that(path, none(), "Bonsai type requires user_id — no global bonsai pages")


def should_return_none_for_bonsai_without_entity():
    path = _build_observation_path("bonsai", "", "user123")
    assert_that(path, none(), "Bonsai path requires a non-empty entity name")


async def should_write_wiki_page_on_successful_classification():
    classify = AsyncMock(return_value={"type": "bonsai", "entity_name": "Tanaka"})
    enrich = AsyncMock(return_value="# Tanaka\n\nHojas amarillas.")
    read_page = MagicMock(return_value={"status": "not_found"})
    write_page = MagicMock()

    await execute_integrate_observations(
        observations=[{"user_id": "user1", "content": "Tanaka tiene hojas amarillas"}],
        classify_observation=classify,
        enrich_wiki_page=enrich,
        read_wiki_page_func=read_page,
        write_wiki_page_func=write_page,
    )

    write_page.assert_called_once_with(path="users/user1/bonsai/tanaka/index.md", content="# Tanaka\n\nHojas amarillas.")


async def should_skip_observation_when_classification_returns_none():
    classify = AsyncMock(return_value=None)
    write_page = MagicMock()

    await execute_integrate_observations(
        observations=[{"user_id": "user1", "content": "algo"}],
        classify_observation=classify,
        enrich_wiki_page=AsyncMock(),
        read_wiki_page_func=MagicMock(),
        write_wiki_page_func=write_page,
    )

    write_page.assert_not_called()


async def should_skip_observation_when_type_is_ignore():
    classify = AsyncMock(return_value={"type": "ignore", "entity_name": ""})
    write_page = MagicMock()

    await execute_integrate_observations(
        observations=[{"user_id": "user1", "content": "algo irrelevante"}],
        classify_observation=classify,
        enrich_wiki_page=AsyncMock(),
        read_wiki_page_func=MagicMock(),
        write_wiki_page_func=write_page,
    )

    write_page.assert_not_called()


async def should_skip_observation_when_classify_raises():
    classify = AsyncMock(side_effect=RuntimeError("LLM error"))
    write_page = MagicMock()

    await execute_integrate_observations(
        observations=[{"user_id": "user1", "content": "algo"}],
        classify_observation=classify,
        enrich_wiki_page=AsyncMock(),
        read_wiki_page_func=MagicMock(),
        write_wiki_page_func=write_page,
    )

    write_page.assert_not_called()


async def should_pass_existing_content_to_enrich_when_page_exists():
    classify = AsyncMock(return_value={"type": "species", "entity_name": "ficus"})
    enrich = AsyncMock(return_value="# Ficus\n\nContenido enriquecido.")
    read_page = MagicMock(return_value={"status": "success", "content": "# Ficus\n\nContenido previo."})
    write_page = MagicMock()

    await execute_integrate_observations(
        observations=[{"user_id": None, "content": "El ficus es resistente"}],
        classify_observation=classify,
        enrich_wiki_page=enrich,
        read_wiki_page_func=read_page,
        write_wiki_page_func=write_page,
    )

    assert_that(enrich.called, equal_to(True), "Enrich should be called")
    call_args = enrich.call_args
    second_arg = call_args.args[1] if len(call_args.args) > 1 else call_args.kwargs.get("existing_content", "")
    assert_that(second_arg, contains_string("Contenido previo."))
