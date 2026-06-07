from hamcrest import assert_that, equal_to, none

from knowledge_base.wiki_index.indexer import _extract_user_id_from_path


def should_extract_user_id_from_user_scoped_path():
    page_path = "users/user123/bonsai/ficus/index.md"

    user_id = _extract_user_id_from_path(page_path)

    assert_that(user_id, equal_to("user123"), "Should extract user_id from users/{user_id}/... path")


def should_return_none_for_global_path():
    page_path = "species/ficus.md"

    user_id = _extract_user_id_from_path(page_path)

    assert_that(user_id, none(), "Should return None for global wiki paths")


def should_return_none_for_techniques_path():
    page_path = "techniques/alambrado.md"

    user_id = _extract_user_id_from_path(page_path)

    assert_that(user_id, none(), "Should return None for techniques global path")


def should_extract_user_id_from_species_notes_path():
    page_path = "users/abc456/species-notes/juniperus.md"

    user_id = _extract_user_id_from_path(page_path)

    assert_that(user_id, equal_to("abc456"), "Should extract user_id from user species-notes path")
