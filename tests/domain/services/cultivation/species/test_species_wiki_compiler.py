import pytest

from bonsai_sensei.domain.services.cultivation.species.species_wiki_compiler import create_write_wiki_page_tool


def should_write_file_and_return_success(wiki_root):
    write = create_write_wiki_page_tool(wiki_root)
    result = write("species/elm.md", "# Elm\n\n## Riego\nContent.")

    assert result == {"status": "success", "path": "species/elm.md"}, (
        "write_wiki_page should return success with the written path"
    )


def should_create_file_at_given_path(wiki_root):
    write = create_write_wiki_page_tool(wiki_root)
    write("species/elm.md", "# Elm")

    assert (wiki_root / "species" / "elm.md").exists(), (
        "write_wiki_page should create the file at the specified path"
    )


def should_create_parent_directories_if_missing(wiki_root):
    write = create_write_wiki_page_tool(wiki_root)
    write("species/nested/dir/elm.md", "# Elm")

    assert (wiki_root / "species" / "nested" / "dir" / "elm.md").exists(), (
        "write_wiki_page should create missing parent directories"
    )


def should_write_file_content(wiki_root):
    write = create_write_wiki_page_tool(wiki_root)
    write("species/elm.md", "# Elm\n\n## Riego\nWater regularly.")

    content = (wiki_root / "species" / "elm.md").read_text()
    assert "Water regularly." in content, (
        "write_wiki_page should write the provided content to the file"
    )


def should_reject_path_traversal_outside_wiki_root(wiki_root):
    write = create_write_wiki_page_tool(wiki_root)
    result = write("../../etc/passwd", "malicious content")

    assert result == {"status": "error", "message": "invalid_path"}, (
        "write_wiki_page should reject paths that escape the wiki root"
    )


def should_not_create_file_on_path_traversal(wiki_root):
    write = create_write_wiki_page_tool(wiki_root)
    write("../../evil.md", "malicious content")

    assert not (wiki_root / "../../evil.md").resolve().exists(), (
        "write_wiki_page should not create any file when path traversal is detected"
    )


@pytest.fixture
def wiki_root(tmp_path):
    return tmp_path
