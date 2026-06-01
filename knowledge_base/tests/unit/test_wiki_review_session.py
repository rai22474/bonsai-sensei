from hamcrest import assert_that, equal_to, contains_inanyorder, empty

from knowledge_base.wiki_review_session import WikiReviewSession


def should_not_be_complete_when_pending_pages_remain():
    session = WikiReviewSession(
        review_id="abc",
        commit_hash="deadbeef",
        pending=["page1.md", "page2.md"],
    )

    assert_that(session.is_complete, equal_to(False), "Session with pending pages should not be complete")


def should_be_complete_when_no_pending_pages():
    session = WikiReviewSession(
        review_id="abc",
        commit_hash="deadbeef",
        pending=[],
    )

    assert_that(session.is_complete, equal_to(True), "Session with no pending pages should be complete")


def should_move_page_to_confirmed_when_resolved_without_revert():
    session = WikiReviewSession(
        review_id="abc",
        commit_hash="deadbeef",
        pending=["page1.md", "page2.md"],
    )

    session.resolve_page("page1.md", reverted=False)

    assert_that(session.confirmed, equal_to(["page1.md"]), "Resolved page should appear in confirmed list")


def should_remove_resolved_page_from_pending():
    session = WikiReviewSession(
        review_id="abc",
        commit_hash="deadbeef",
        pending=["page1.md", "page2.md"],
    )

    session.resolve_page("page1.md", reverted=False)

    assert_that(session.pending, equal_to(["page2.md"]), "Resolved page should be removed from pending")


def should_move_page_to_reverted_when_resolved_with_revert():
    session = WikiReviewSession(
        review_id="abc",
        commit_hash="deadbeef",
        pending=["page1.md"],
    )

    session.resolve_page("page1.md", reverted=True)

    assert_that(session.reverted, equal_to(["page1.md"]), "Reverted page should appear in reverted list")


def should_be_complete_after_all_pages_resolved():
    session = WikiReviewSession(
        review_id="abc",
        commit_hash="deadbeef",
        pending=["page1.md", "page2.md"],
    )

    session.resolve_page("page1.md", reverted=False)
    session.resolve_page("page2.md", reverted=True)

    assert_that(session.is_complete, equal_to(True), "Session should be complete after all pages resolved")


def should_not_fail_when_resolving_page_not_in_pending():
    session = WikiReviewSession(
        review_id="abc",
        commit_hash="deadbeef",
        pending=["page1.md"],
    )

    session.resolve_page("nonexistent.md", reverted=False)

    assert_that(session.pending, equal_to(["page1.md"]), "Pending list should be unchanged for unknown page")
