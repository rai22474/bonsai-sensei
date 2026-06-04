import uuid
import pytest
from http_client import delete, post


@pytest.fixture
def context():
    return {
        "user_id": f"bdd-dreamer-cards-{uuid.uuid4().hex}",
        "wiki_paths_created": [],
        "card_paths_created": [],
    }


@pytest.fixture(autouse=True)
def reset_dreamer_watermark():
    post("/api/wiki/transcripts/wiki-dreamer/watermark/reset")
    yield


@pytest.fixture(autouse=True)
def cleanup_records(context):
    yield
    for card_path in context["card_paths_created"]:
        try:
            delete(f"/api/wiki/transcripts/cards?path={card_path}")
        except Exception:
            pass
    for wiki_path in context["wiki_paths_created"]:
        try:
            delete(f"/api/wiki?path={wiki_path}")
        except Exception:
            pass
