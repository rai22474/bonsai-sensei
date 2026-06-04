import pytest

from http_client import get, reset_session


@pytest.fixture(scope="session", autouse=True)
def assert_service_healthy():
    """Fail fast if the bonsai_sensei service is not reachable before running any test."""
    try:
        response = get("/health")
        assert response.get("status") == "ok", f"Health check returned unexpected response: {response}"
    except Exception as error:
        pytest.fail(f"bonsai_sensei service is not healthy — acceptance tests cannot run: {error}")


@pytest.fixture(autouse=True)
def reset_adk_session_after_test(context):
    yield
    user_id = context.get("user_id")
    if user_id:
        reset_session(user_id)
