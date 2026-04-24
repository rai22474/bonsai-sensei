import pytest

from bonsai_sensei.domain.services.wiki_page_tool import create_read_wiki_page_tool


def should_return_file_content_when_page_exists(wiki_root):
    page = wiki_root / "species" / "elm.md"
    page.parent.mkdir(parents=True)
    page.write_text("# Elm\n\n## Riego\nRegar moderadamente.")

    tool = create_read_wiki_page_tool(str(wiki_root))
    result = tool(path="species/elm.md")

    assert result == {"status": "success", "content": "# Elm\n\n## Riego\nRegar moderadamente."}, (
        "Tool should return the file content when the page exists"
    )


def should_return_error_when_page_does_not_exist(wiki_root):
    tool = create_read_wiki_page_tool(str(wiki_root))
    result = tool(path="species/nonexistent.md")

    assert result == {"status": "error", "message": "page_not_found"}, (
        "Tool should return page_not_found error when the file does not exist"
    )


def should_prevent_path_traversal_outside_wiki_root(wiki_root):
    tool = create_read_wiki_page_tool(str(wiki_root))
    result = tool(path="../../etc/passwd")

    assert result == {"status": "error", "message": "invalid_path"}, (
        "Tool should reject paths that escape the wiki root"
    )


@pytest.fixture
def wiki_root(tmp_path):
    return tmp_path
