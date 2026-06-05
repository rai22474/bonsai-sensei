import functools
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from hamcrest import assert_that, equal_to

from knowledge_base.dreamer.runner import (
    _add_wikilinks,
    _enrich_from_knowledge_cards,
    _integrate_observations,
    run_wiki_dreamer,
)

_NOW = datetime(2026, 6, 5, tzinfo=timezone.utc)


def _phases_run(mock_run_phase: Mock) -> list[str]:
    return [c.args[3] for c in mock_run_phase.call_args_list]


def _make_phases(agent):
    return {
        "integrate_observations": functools.partial(_integrate_observations, agent),
        "enrich_from_knowledge_cards": functools.partial(_enrich_from_knowledge_cards, agent),
        "add_wikilinks": functools.partial(_add_wikilinks, agent),
    }


async def should_run_no_phases_when_no_work(mock_agent, mock_commit):
    with patch("knowledge_base.dreamer.runner._run_phase") as run_phase:
        await run_wiki_dreamer(
            read_observations=AsyncMock(return_value=[]),
            read_new_cards=Mock(return_value=[]),
            read_wikilinks_batch=Mock(return_value=[]),
            read_last_run=Mock(return_value=_NOW),
            **_make_phases(mock_agent),
            save_run_state=Mock(),
            commit_and_notify=mock_commit,
        )

    assert_that(_phases_run(run_phase), equal_to([]))


async def should_run_only_observations_phase_when_only_observations_present(mock_agent, mock_commit):
    with patch("knowledge_base.dreamer.runner._run_phase") as run_phase:
        await run_wiki_dreamer(
            read_observations=AsyncMock(return_value=["Eren tiene ramas amarillas"]),
            read_new_cards=Mock(return_value=[]),
            read_wikilinks_batch=Mock(return_value=[]),
            read_last_run=Mock(return_value=_NOW),
            **_make_phases(mock_agent),
            save_run_state=Mock(),
            commit_and_notify=mock_commit,
        )

    assert_that(_phases_run(run_phase), equal_to(["integrate observations"]))


async def should_run_only_cards_phase_when_only_new_cards_present(mock_agent, mock_commit):
    with patch("knowledge_base.dreamer.runner._run_phase") as run_phase:
        await run_wiki_dreamer(
            read_observations=AsyncMock(return_value=[]),
            read_new_cards=Mock(return_value=["junipero.md"]),
            read_wikilinks_batch=Mock(return_value=[]),
            read_last_run=Mock(return_value=_NOW),
            **_make_phases(mock_agent),
            save_run_state=Mock(),
            commit_and_notify=mock_commit,
        )

    assert_that(_phases_run(run_phase), equal_to(["enrich from knowledge cards"]))


async def should_run_only_wikilinks_phase_when_only_pending_pages_present(mock_agent, mock_commit):
    with patch("knowledge_base.dreamer.runner._run_phase") as run_phase:
        await run_wiki_dreamer(
            read_observations=AsyncMock(return_value=[]),
            read_new_cards=Mock(return_value=[]),
            read_wikilinks_batch=Mock(return_value=["species/junipero.md"]),
            read_last_run=Mock(return_value=_NOW),
            **_make_phases(mock_agent),
            save_run_state=Mock(),
            commit_and_notify=mock_commit,
        )

    assert_that(_phases_run(run_phase), equal_to(["add wikilinks"]))


async def should_run_all_phases_in_order_when_all_inputs_present(mock_agent, mock_commit):
    with patch("knowledge_base.dreamer.runner._run_phase") as run_phase:
        await run_wiki_dreamer(
            read_observations=AsyncMock(return_value=["Eren tiene ramas amarillas"]),
            read_new_cards=Mock(return_value=["junipero.md"]),
            read_wikilinks_batch=Mock(return_value=["species/junipero.md"]),
            read_last_run=Mock(return_value=_NOW),
            **_make_phases(mock_agent),
            save_run_state=Mock(),
            commit_and_notify=mock_commit,
        )

    assert_that(
        _phases_run(run_phase),
        equal_to(["integrate observations", "enrich from knowledge cards", "add wikilinks"]),
    )


async def should_call_save_run_state_after_phases(mock_agent, mock_commit):
    save_run_state = Mock()
    with patch("knowledge_base.dreamer.runner._run_phase"):
        await run_wiki_dreamer(
            read_observations=AsyncMock(return_value=[]),
            read_new_cards=Mock(return_value=[]),
            read_wikilinks_batch=Mock(return_value=["species/junipero.md"]),
            read_last_run=Mock(return_value=_NOW),
            **_make_phases(mock_agent),
            save_run_state=save_run_state,
            commit_and_notify=mock_commit,
        )

    assert_that(save_run_state.called, equal_to(True))


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.name = "test_agent"
    return agent


@pytest.fixture
def mock_commit():
    return AsyncMock()
