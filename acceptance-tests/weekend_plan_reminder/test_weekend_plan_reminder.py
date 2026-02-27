from pytest_bdd import scenario, when, then, parsers

from http_client import post_sse

TEST_USER_ID = "weekend-reminder-test-user"


@scenario(
    "../features/weekend_plan_reminder.feature",
    "User with planned works receives a weekend summary",
)
def test_user_with_planned_works():
    return None


@scenario(
    "../features/weekend_plan_reminder.feature",
    "User with no planned works receives a positive message",
)
def test_user_with_no_planned_works():
    return None


@when("the weekend plan reminder triggers")
def trigger_weekend_reminder(context):
    events = post_sse("/api/cultivation/plan/weekend-reminder/trigger")
    context["sse_events"] = events


@then(parsers.parse('the response for "{user_id}" mentions "{expected_text}"'))
def assert_response_mentions(context, user_id, expected_text):
    user_event = _find_user_event(context["sse_events"], user_id)
    response_text = user_event.get("response", "")
    assert expected_text in response_text, (
        f"Expected response for '{user_id}' to mention '{expected_text}', "
        f"but got: {response_text}"
    )


@then(parsers.parse('the response for "{user_id}" is non-empty'))
def assert_response_non_empty(context, user_id):
    user_event = _find_user_event(context["sse_events"], user_id)
    response_text = user_event.get("response", "")
    assert len(response_text) > 0, (
        f"Expected a non-empty response for user '{user_id}', "
        f"but got an empty string. SSE events: {context['sse_events']}"
    )


def _find_user_event(sse_events: list[dict], user_id: str) -> dict:
    user_event = next(
        (event for event in sse_events if event.get("user_id") == user_id),
        None,
    )
    assert user_event is not None, (
        f"Expected an SSE event for user_id='{user_id}', but none found. "
        f"Got events: {sse_events}"
    )
    return user_event
