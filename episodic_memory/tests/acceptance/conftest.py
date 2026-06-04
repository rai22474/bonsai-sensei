import pytest
from http_client import get


@pytest.fixture(scope="session", autouse=True)
def assert_service_healthy():
    try:
        response = get("/health")
        assert response.get("status") == "ok", f"Health check returned unexpected response: {response}"
    except Exception as error:
        pytest.fail(f"episodic-memory service is not healthy — acceptance tests cannot run: {error}")
