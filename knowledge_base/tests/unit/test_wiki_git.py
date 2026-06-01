import subprocess

import pytest
from hamcrest import assert_that, equal_to, not_none, none, contains_string

from knowledge_base.wiki_git import (
    commit_wiki_changes,
    get_changed_files,
    get_page_diff,
    init_wiki_repo,
    revert_page,
)


def should_create_git_repo_when_directory_has_no_git(wiki_root):
    init_wiki_repo(wiki_root)

    assert_that((wiki_root / ".git").exists(), equal_to(True), "init_wiki_repo should create a .git directory")


def should_not_fail_when_repo_already_initialized(wiki_root):
    init_wiki_repo(wiki_root)
    init_wiki_repo(wiki_root)

    assert_that((wiki_root / ".git").exists(), equal_to(True), "Calling init twice should leave repo intact")


def should_return_none_when_nothing_to_commit(wiki_root):
    init_wiki_repo(wiki_root)

    result = commit_wiki_changes(wiki_root, "empty commit")

    assert_that(result, none(), "Should return None when there are no staged changes")


def should_return_commit_hash_when_changes_exist(wiki_root):
    init_wiki_repo(wiki_root)
    (wiki_root / "page.md").write_text("# New page")

    commit_hash = commit_wiki_changes(wiki_root, "add page")

    assert_that(commit_hash, not_none(), "Should return a commit hash when changes are committed")
    assert_that(len(commit_hash), equal_to(40), "Commit hash should be 40 hex characters")


def should_list_files_changed_in_commit(wiki_root):
    init_wiki_repo(wiki_root)
    (wiki_root / "species.md").write_text("# Ficus")
    (wiki_root / "techniques.md").write_text("# Wiring")
    commit_hash = commit_wiki_changes(wiki_root, "add two pages")

    changed = get_changed_files(wiki_root, commit_hash)

    assert_that(sorted(changed), equal_to(["species.md", "techniques.md"]),
        "Should list all files added in the commit")


def should_return_diff_for_modified_page(wiki_root):
    init_wiki_repo(wiki_root)
    page = wiki_root / "page.md"
    page.write_text("# Original content")
    commit_wiki_changes(wiki_root, "initial")
    page.write_text("# Original content\n\n## New section")
    commit_hash = commit_wiki_changes(wiki_root, "add section")

    diff = get_page_diff(wiki_root, "page.md", commit_hash)

    assert_that(diff, contains_string("New section"), "Diff should contain the added content")


def should_return_empty_string_when_page_not_in_commit(wiki_root):
    init_wiki_repo(wiki_root)
    (wiki_root / "other.md").write_text("# Other")
    commit_hash = commit_wiki_changes(wiki_root, "add other")

    diff = get_page_diff(wiki_root, "page.md", commit_hash)

    assert_that(diff.strip(), equal_to(""), "Diff should be empty for unmodified page")


def should_restore_page_to_previous_version_on_revert(wiki_root):
    init_wiki_repo(wiki_root)
    page = wiki_root / "page.md"
    page.write_text("# Version 1")
    commit_wiki_changes(wiki_root, "initial")
    page.write_text("# Version 2")
    commit_hash = commit_wiki_changes(wiki_root, "update")

    revert_page(wiki_root, "page.md", commit_hash)

    assert_that(page.read_text(), equal_to("# Version 1"),
        "Page should be restored to its content before the given commit")


def should_delete_page_when_reverting_its_creation(wiki_root):
    init_wiki_repo(wiki_root)
    page = wiki_root / "new_page.md"
    page.write_text("# Brand new")
    commit_hash = commit_wiki_changes(wiki_root, "create page")

    revert_page(wiki_root, "new_page.md", commit_hash)

    assert_that(page.exists(), equal_to(False),
        "Page should be deleted when reverting its creation commit")


@pytest.fixture
def wiki_root(tmp_path):
    subprocess.run(
        ["git", "config", "--global", "user.email", "test@test.com"],
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "--global", "user.name", "Test"],
        capture_output=True,
    )
    return tmp_path
