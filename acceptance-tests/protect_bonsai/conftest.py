import uuid

import pytest


@pytest.fixture
def context():
    return {
        "user_id": f"bdd-protect-{uuid.uuid4().hex}",
    }
