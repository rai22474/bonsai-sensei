import pytest
from hamcrest import assert_that, equal_to, has_item, not_
from pytest_bdd import given, parsers, scenario, then, when

from http_client import delete, get, post, put


@scenario("../features/wiki_review.feature", "Admin confirms a page changed by the dreamer")
def test_admin_confirms_page():
    return None


@scenario("../features/wiki_review.feature", "Admin reverts a page changed by the dreamer")
def test_admin_reverts_page():
    return None


@given(parsers.parse('a wiki page "{page_path}" with content "{content}"'))
def create_wiki_page(context, page_path, content):
    put("/api/wiki", {"path": page_path, "content": content})
    context["wiki_paths_created"].append(page_path)


@when("a review session is created for the uncommitted wiki changes")
def create_review_session(context):
    session = post("/api/wiki/review/sessions")
    context["review_session_id"] = session["review_id"]


@then(parsers.parse('the review session has "{page_path}" as pending'))
def assert_page_in_pending(context, page_path):
    session = get(f"/api/wiki/review/sessions/{context['review_session_id']}")
    assert_that(session["pending"], has_item(page_path),
        f"Page {page_path} should be in the pending list")


@when(parsers.parse("the admin confirms page {page_index:d} of the review session"))
def confirm_page(context, page_index):
    result = post(f"/api/wiki/review/sessions/{context['review_session_id']}/pages/{page_index}/confirm")
    context["last_session_state"] = result


@when(parsers.parse("the admin reverts page {page_index:d} of the review session"))
def revert_page(context, page_index):
    result = post(f"/api/wiki/review/sessions/{context['review_session_id']}/pages/{page_index}/revert")
    context["last_session_state"] = result


@then(parsers.parse('"{page_path}" is in the confirmed list'))
def assert_page_confirmed(context, page_path):
    session = context["last_session_state"]
    assert_that(session["confirmed"], has_item(page_path),
        f"Page {page_path} should be in the confirmed list")


@then(parsers.parse('"{page_path}" is no longer pending'))
def assert_page_not_pending(context, page_path):
    session = context["last_session_state"]
    assert_that(session["pending"], not_(has_item(page_path)),
        f"Page {page_path} should not be in the pending list")


@then(parsers.parse('the wiki page "{page_path}" no longer exists'))
def assert_wiki_page_deleted(context, page_path):
    try:
        get(f"/api/wiki?path={page_path}")
        raise AssertionError(f"Wiki page {page_path} should not exist after revert")
    except Exception as error:
        assert_that("404" in str(error) or "page_not_found" in str(error), equal_to(True),
            f"Expected 404 for reverted page {page_path}, got: {error}")
