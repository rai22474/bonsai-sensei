from hamcrest import assert_that, contains_string, not_, not_none, none, has_item

from pytest_bdd import given, parsers, scenario, then, when

from mcp_client import read_wiki_page, write_wiki_page, list_wiki_files
from http_client import delete


@scenario("../features/wiki_crud.feature", "Write and read a wiki page")
def test_write_and_read():
    return None


@scenario("../features/wiki_crud.feature", "Overwrite an existing wiki page")
def test_overwrite():
    return None


@scenario("../features/wiki_crud.feature", "Delete a wiki page")
def test_delete():
    return None


@scenario("../features/wiki_crud.feature", "List wiki pages in a directory")
def test_list():
    return None


@scenario("../features/wiki_crud.feature", "Read a non-existent wiki page returns not found")
def test_read_missing():
    return None


@given(parsers.parse('no wiki page exists at "{page_path}"'))
def ensure_page_absent(context, page_path):
    try:
        delete(f"/api/wiki?path={page_path}")
    except Exception:
        pass


@given(parsers.parse('a wiki page "{page_path}" exists with content "{content}"'))
def create_wiki_page(context, page_path, content):
    write_wiki_page(page_path, content)
    context["wiki_paths_created"].append(page_path)


@when(parsers.parse('a wiki page "{page_path}" is written with content "{content}"'))
def write_page(context, page_path, content):
    write_wiki_page(page_path, content)
    context["wiki_paths_created"].append(page_path)


@when(parsers.parse('the wiki page "{page_path}" is deleted'))
def delete_page(context, page_path):
    delete(f"/api/wiki?path={page_path}")


@when(parsers.parse('wiki files in "{directory}" are listed'))
def list_files(context, directory):
    context["last_list_result"] = list_wiki_files(directory)


@when(parsers.parse('"{page_path}" is read'))
def read_page(context, page_path):
    context["last_read_result"] = read_wiki_page(page_path)


@then(parsers.parse('reading "{page_path}" returns content containing "{text}"'))
def assert_page_contains(context, page_path, text):
    page = read_wiki_page(page_path)
    assert_that(page, not_none(), f"Page {page_path} should exist")
    assert_that(page.get("content", ""), contains_string(text))


@then(parsers.parse('reading "{page_path}" does not contain "{text}"'))
def assert_page_not_contains(context, page_path, text):
    page = read_wiki_page(page_path)
    assert_that(page.get("content", ""), not_(contains_string(text)))


@then(parsers.parse('the wiki page "{page_path}" does not exist'))
def assert_page_absent(context, page_path):
    page = read_wiki_page(page_path)
    assert_that(page, none(), f"Page {page_path} should not exist")


@then(parsers.parse('the file list contains "{page_path}"'))
def assert_file_in_list(context, page_path):
    assert_that(context["last_list_result"], has_item(page_path),
        f"{page_path} should appear in file list")


@then("the result indicates the page was not found")
def assert_not_found(context):
    assert_that(context["last_read_result"], none(), "Missing page should return None")
