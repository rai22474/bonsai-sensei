import uuid

import pytest
from pytest_bdd import given, parsers

from http_client import delete, post


@pytest.fixture
def context():
    return {
        "user_id": f"bdd-episodic-memory-{uuid.uuid4().hex}",
        "wiki_paths_created": [],
    }


@pytest.fixture(autouse=True)
def reset_memory_watermark():
    post("/api/wiki/transcripts/wiki-dreamer/watermark/reset")
    yield


@pytest.fixture(autouse=True)
def cleanup_records(context):
    yield
    for wiki_path in context["wiki_paths_created"]:
        try:
            delete(f"/api/wiki?path={wiki_path}")
        except Exception:
            pass


@given(parsers.parse('the episodic memory has an observation "{text}"'))
def submit_observation(context, text):
    post("/api/wiki/transcripts/observations", {"text": text})
