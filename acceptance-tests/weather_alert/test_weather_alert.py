from pytest_bdd import scenario, given, when, then, parsers
from deepeval import assert_test
from deepeval.test_case import LLMTestCase

from http_client import post_sse, put
from judge import create_recommendation_metric

FROST_CRITERIA = (
    "The response should mention frost or freezing risk and recommend protecting the bonsais."
)


@scenario(
    "../features/weather_alert.feature",
    "Sensei evaluates frost risk and recommends action for registered user",
)
def test_frost_alert():
    return None


@scenario(
    "../features/weather_alert.feature",
    "Sensei confirms safe weather for registered user",
)
def test_safe_weather():
    return None


@given(
    parsers.parse(
        'user "{user_id}" has location "{location}" registered with chat id "{chat_id}"'
    )
)
def register_user_settings(context, user_id, location, chat_id):
    put(
        f"/api/users/{user_id}/settings",
        {"location": location, "telegram_chat_id": chat_id},
    )
    context["user_id"] = user_id
    context["location"] = location


@when(parsers.parse('the daily weather alert check runs with frost conditions for "{location}"'))
def trigger_alert_with_frost(context, location, frost_weather_server):
    events = post_sse("/api/weather/alerts/trigger")
    context["sse_events"] = events


@when(parsers.parse('the daily weather alert check runs with safe conditions for "{location}"'))
def trigger_alert_with_safe(context, location, safe_weather_server):
    events = post_sse("/api/weather/alerts/trigger")
    context["sse_events"] = events


@then(parsers.parse('the sensei response for "{user_id}" mentions frost risk'))
def assert_frost_mentioned(context, user_id):
    user_event = _find_user_event(context["sse_events"], user_id)
    response_text = user_event.get("response", "")
    test_case = LLMTestCase(
        input=context.get("location", ""),
        actual_output=response_text,
    )
    metric = create_recommendation_metric("weather_frost_alert", FROST_CRITERIA)
    assert_test(test_case=test_case, metrics=[metric], run_async=False)


@then(parsers.parse('the sensei response for "{user_id}" is non-empty'))
def assert_response_non_empty(context, user_id):
    user_event = _find_user_event(context["sse_events"], user_id)
    response_text = user_event.get("response", "")
    assert len(response_text) > 0, (
        f"Expected a non-empty sensei response for user '{user_id}', but got an empty string. "
        f"SSE events: {context['sse_events']}"
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
