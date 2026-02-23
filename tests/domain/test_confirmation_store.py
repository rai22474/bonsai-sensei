import pytest
from hamcrest import assert_that, equal_to, none, not_none

from bonsai_sensei.domain.confirmation import Confirmation
from bonsai_sensei.domain.confirmation_store import ConfirmationStore


def _make_confirmation(deduplication_key: str | None = None) -> Confirmation:
    return Confirmation(
        id="test-id",
        user_id="user-1",
        summary="Test",
        executor=lambda: None,
        deduplication_key=deduplication_key,
    )


def should_store_confirmation_without_deduplication_key(store):
    first = _make_confirmation(deduplication_key=None)
    second = _make_confirmation(deduplication_key=None)

    store.set_pending("user-1", first)
    store.set_pending("user-1", second)

    assert_that(
        len(store.get_all_pending("user-1")),
        equal_to(2),
        "Confirmations without a deduplication key should always be appended",
    )


def should_skip_second_confirmation_with_same_deduplication_key(store):
    first = _make_confirmation(deduplication_key="create_species:Ficus")
    second = _make_confirmation(deduplication_key="create_species:Ficus")

    store.set_pending("user-1", first)
    store.set_pending("user-1", second)

    assert_that(
        len(store.get_all_pending("user-1")),
        equal_to(1),
        "A second confirmation with the same deduplication key should be skipped",
    )


def should_store_confirmations_with_different_deduplication_keys(store):
    first = _make_confirmation(deduplication_key="create_species:Ficus")
    second = _make_confirmation(deduplication_key="create_species:Elm")

    store.set_pending("user-1", first)
    store.set_pending("user-1", second)

    assert_that(
        len(store.get_all_pending("user-1")),
        equal_to(2),
        "Confirmations with different deduplication keys should both be stored",
    )


def should_not_deduplicate_across_different_users(store):
    first = _make_confirmation(deduplication_key="create_species:Ficus")
    second = Confirmation(
        id="other-id",
        user_id="user-2",
        summary="Other",
        executor=lambda: None,
        deduplication_key="create_species:Ficus",
    )

    store.set_pending("user-1", first)
    store.set_pending("user-2", second)

    assert_that(
        store.get_pending("user-1"),
        not_none(),
        "user-1 should have a pending confirmation",
    )
    assert_that(
        store.get_pending("user-2"),
        not_none(),
        "user-2 should have a pending confirmation independently",
    )


def should_allow_same_key_after_first_confirmation_is_popped(store):
    first = _make_confirmation(deduplication_key="create_species:Ficus")
    second = _make_confirmation(deduplication_key="create_species:Ficus")

    store.set_pending("user-1", first)
    store.pop_pending("user-1")
    store.set_pending("user-1", second)

    assert_that(
        store.get_pending("user-1"),
        not_none(),
        "After popping, a new confirmation with the same key should be accepted",
    )


def should_keep_first_confirmation_when_duplicate_is_skipped(store):
    first = _make_confirmation(deduplication_key="delete_bonsai:Naruto")
    second = _make_confirmation(deduplication_key="delete_bonsai:Naruto")

    store.set_pending("user-1", first)
    store.set_pending("user-1", second)

    stored = store.get_pending("user-1")
    assert_that(
        stored.id,
        equal_to("test-id"),
        "The stored confirmation should be the first one, not the duplicate",
    )


@pytest.fixture
def store():
    return ConfirmationStore()
