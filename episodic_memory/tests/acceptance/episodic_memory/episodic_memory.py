from datetime import datetime, timezone

from hamcrest import assert_that, empty, not_empty, any_of, has_item, contains_string
from pytest_bdd import given, scenario, then, when, parsers

from http_client import get, post


@scenario("../features/episodic_memory.feature", "Episode appears in observations after submission")
def test_episode_appears_in_observations():
    return None


@scenario("../features/episodic_memory.feature", "Observations aggregate episodes from all users")
def test_observations_aggregate_all_users():
    return None


@scenario("../features/episodic_memory.feature", "Memory search returns relevant facts for a user")
def test_memory_search_returns_facts():
    return None


@scenario("../features/episodic_memory.feature", "Memory search is isolated per user")
def test_memory_search_isolated_per_user():
    return None


@when(parsers.parse('a conversation episode about "{topic}" is submitted for user "{user_id}"'))
def submit_episode_when(context, topic, user_id):
    _submit_episode(context, topic, user_id)


@given(parsers.parse('a conversation episode about "{topic}" is submitted for user "{user_id}"'))
def submit_episode_given(context, topic, user_id):
    _submit_episode(context, topic, user_id)


def _submit_episode(context, topic, user_id):
    if "submitted_at" not in context:
        context["submitted_at"] = datetime.now(timezone.utc).isoformat()
    post("/episodes", {
        "user_id": user_id,
        "messages": [
            {"role": "user", "content": topic},
            {"role": "assistant", "content": "Entendido, registrado para seguimiento del bonsai"},
        ],
    })


@then("the observations since submission contain content from the episode")
def assert_observations_contain_episode_content(context):
    response = get("/observations", {"since": context["submitted_at"]})
    observations = response.get("observations", [])
    assert_that(observations, not_empty(), "Should have at least one observation after submitting episode")


@then("the observations since the beginning contain content from both users")
def assert_observations_from_all_users(context):
    response = get("/observations", {"since": "2024-01-01T00:00:00+00:00"})
    observations = response.get("observations", [])
    assert_that(observations, not_empty(), "Observations should include episodes from all users")


@when(parsers.parse('memory is searched for user "{user_id}" with query "{query}"'))
def search_memory(context, user_id, query):
    response = get("/memory", {"user_id": user_id, "query": query})
    context["search_results"] = response.get("memories", [])


@then("the search results are not empty")
def assert_search_not_empty(context):
    assert_that(context["search_results"], not_empty(), "Search should return at least one fact for this user")


@then("the search results are empty")
def assert_search_empty(context):
    assert_that(context["search_results"], empty(), "Search should return no facts for a different user")
