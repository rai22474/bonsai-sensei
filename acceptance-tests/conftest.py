import pytest

from http_client import reset_session


@pytest.fixture(autouse=True)
def reset_adk_session_after_test(context):
    yield
    user_id = context.get("user_id")
    if user_id:
        reset_session(user_id)
