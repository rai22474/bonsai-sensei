import uuid
import pytest
from http_client import delete


@pytest.fixture
def context():
    return {
        "user_id": f"bdd-wiki-crud-{uuid.uuid4().hex}",
        "wiki_paths_created": [],
        "last_read_result": None,
        "last_list_result": None,
    }


@pytest.fixture(autouse=True)
def cleanup_records(context):
    yield
    for wiki_path in context["wiki_paths_created"]:
        try:
            delete(f"/api/wiki?path={wiki_path}")
        except Exception:
            pass
