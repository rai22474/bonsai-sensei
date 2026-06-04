import uuid
import pytest
from http_client import delete
from mcp_client import write_wiki_page


@pytest.fixture
def context():
    return {
        "user_id": f"bdd-wiki-editor-{uuid.uuid4().hex}",
        "wiki_paths_created": [],
        "editor_response": "",
    }


@pytest.fixture(autouse=True)
def cleanup_records(context):
    yield
    for wiki_path in context["wiki_paths_created"]:
        try:
            delete(f"/api/wiki?path={wiki_path}")
        except Exception:
            pass
