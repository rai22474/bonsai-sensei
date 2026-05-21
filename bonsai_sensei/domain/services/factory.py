import os
from functools import partial

from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.tools import AgentTool
from google.adk.tools.preload_memory_tool import preload_memory_tool

from bonsai_sensei.domain import bonsai_history
from bonsai_sensei.domain import bonsai_photo_store
from bonsai_sensei.domain import cultivation_plan
from bonsai_sensei.domain import fertilizer_catalog
from bonsai_sensei.domain import garden
from bonsai_sensei.domain import herbarium
from bonsai_sensei.domain import pest_catalog
from bonsai_sensei.domain import phytosanitary_registry
from bonsai_sensei.domain import user_settings_store
from bonsai_sensei.domain.services.cultivation.plan.planned_work_tools import (
    create_list_planned_works_tool,
)
from bonsai_sensei.domain.services.cultivation.species.herbarium_tools import (
    create_list_species_tool,
)
from bonsai_sensei.domain.services.garden.nursery.bonsai_tools import (
    create_get_bonsai_by_name_tool,
    create_list_bonsai_tool,
)
from bonsai_sensei.domain.services.garden.caretaker.bonsai_events_tool import create_list_bonsai_events_tool
from bonsai_sensei.domain.services.cultivation.pests.pest_tools import create_list_pests_tool
from bonsai_sensei.domain.services.garden.gallery.list_bonsai_photos import (
    create_list_bonsai_photos_tool,
    create_show_bonsai_photos_tool,
)
from bonsai_sensei.domain.services.garden.gallery.show_bonsai_photo import create_show_bonsai_photo_tool
from bonsai_sensei.domain.services.cultivation.weather.weather import create_weather_tool
from bonsai_sensei.domain.services.cultivation.weather.weather_risk_tool import (
    create_weather_risk_tool,
    WEATHER_RISK_TOOL_DESCRIPTION,
)
from bonsai_sensei.domain.services.garden.kantei.factory import (
    create_kantei_group,
    ANALYZE_TOOL_DESCRIPTION,
    COMPARE_TOOL_DESCRIPTION,
)
from bonsai_sensei.domain.services.mitori import create_mitori
from bonsai_sensei.domain.services.shokunin import Shokunin
from bonsai_sensei.domain.services.sensei import create_sensei
from bonsai_sensei.domain.services.storekeeper.fertilizers.fertilizer_tools import (
    create_list_fertilizers_tool,
    create_get_fertilizer_by_name_tool,
)
from bonsai_sensei.domain.services.storekeeper.phytosanitary.phytosanitary_tools import (
    create_list_phytosanitary_tool,
    create_get_phytosanitary_by_name_tool,
)


def _build_agent_descriptions(agents) -> list[str]:
    return [f"- {agent.name}: {agent.description}" for agent in agents]


def _create_query_tools(session_factory, wiki_root: str) -> list:
    get_bonsai_by_name_func = partial(garden.get_bonsai_by_name, create_session=session_factory)
    list_species_func = partial(herbarium.list_species, create_session=session_factory)

    list_bonsai_tool = create_list_bonsai_tool(
        list_bonsai_func=partial(garden.list_bonsai, create_session=session_factory),
        list_species_func=list_species_func,
    )
    get_bonsai_by_name_tool = create_get_bonsai_by_name_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_species_func=list_species_func,
    )
    list_bonsai_events_tool = create_list_bonsai_events_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_events_func=partial(bonsai_history.list_bonsai_events, create_session=session_factory),
    )
    list_species_tool = create_list_species_tool(
        get_all_species_func=partial(herbarium.get_all_species, create_session=session_factory),
    )
    list_fertilizers_tool = create_list_fertilizers_tool(
        list_fertilizers_func=partial(fertilizer_catalog.list_fertilizers, create_session=session_factory),
    )
    get_fertilizer_by_name_tool = create_get_fertilizer_by_name_tool(
        get_fertilizer_by_name_func=partial(fertilizer_catalog.get_fertilizer_by_name, create_session=session_factory),
        wiki_root=wiki_root,
    )
    list_phytosanitary_tool = create_list_phytosanitary_tool(
        list_phytosanitary_func=partial(phytosanitary_registry.list_phytosanitary, create_session=session_factory),
    )
    get_phytosanitary_by_name_tool = create_get_phytosanitary_by_name_tool(
        get_phytosanitary_by_name_func=partial(phytosanitary_registry.get_phytosanitary_by_name, create_session=session_factory),
        wiki_root=wiki_root,
    )
    list_planned_works_tool = create_list_planned_works_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_planned_works_func=partial(cultivation_plan.list_planned_works, create_session=session_factory),
    )
    list_planned_works_tool.__name__ = "list_planned_works_for_bonsai"
    list_bonsai_photos_func = partial(bonsai_photo_store.list_bonsai_photos, create_session=session_factory)
    list_bonsai_photos_tool = create_list_bonsai_photos_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_photos_func=list_bonsai_photos_func,
    )
    list_bonsai_photos_tool.__name__ = "list_bonsai_photos"
    show_bonsai_photos_tool = create_show_bonsai_photos_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_photos_func=list_bonsai_photos_func,
    )
    show_bonsai_photos_tool.__name__ = "show_bonsai_photos"
    show_bonsai_photo_tool = create_show_bonsai_photo_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_photos_func=list_bonsai_photos_func,
    )
    show_bonsai_photo_tool.__name__ = "show_bonsai_photo"
    list_pests_tool = create_list_pests_tool(
        list_pests_func=partial(pest_catalog.list_pests, create_session=session_factory),
    )
    list_pests_tool.__name__ = "list_pests"

    return [
        list_bonsai_tool,
        get_bonsai_by_name_tool,
        list_bonsai_events_tool,
        list_species_tool,
        list_fertilizers_tool,
        get_fertilizer_by_name_tool,
        list_phytosanitary_tool,
        get_phytosanitary_by_name_tool,
        list_planned_works_tool,
        list_bonsai_photos_tool,
        show_bonsai_photos_tool,
        show_bonsai_photo_tool,
        list_pests_tool,
    ]


def create_sensei_group(
    model: object,
    command_agents: list,
    session_factory,
    wiki_root: str,
    orchestrator_model: object = None,
):
    effective_orchestrator_model = orchestrator_model or model
    analyze_tool, compare_tool = create_kantei_group(
        model=model,
        session_factory=session_factory,
        orchestrator_model=orchestrator_model,
    )
    weather_risk_tool = create_weather_risk_tool(
        get_user_settings_func=partial(user_settings_store.get_user_settings, create_session=session_factory),
        get_weather_func=create_weather_tool(os.getenv("WEATHER_API_BASE", "https://wttr.in")),
    )
    tool_descriptions = [ANALYZE_TOOL_DESCRIPTION, COMPARE_TOOL_DESCRIPTION, WEATHER_RISK_TOOL_DESCRIPTION]
    callable_tools = {
        "analyze_bonsai_photo": analyze_tool,
        "compare_bonsai_photos": compare_tool,
        "get_weather_risk": weather_risk_tool,
    }
    mitori = create_mitori(
        model=effective_orchestrator_model,
        agent_descriptions=_build_agent_descriptions(command_agents),
        tool_descriptions=tool_descriptions,
    )
    agent_tools = {agent.name: AgentTool(agent) for agent in command_agents}
    executor = Shokunin(
        name="shokunin",
        description="Executes the action plan by calling sub-agents or tools directly.",
        agent_tools=agent_tools,
        callable_tools=callable_tools,
    )
    command_pipeline = SequentialAgent(
        name="command_pipeline",
        sub_agents=[mitori, executor],
    )

    query_tools = _create_query_tools(session_factory, wiki_root)

    return create_sensei(
        model=effective_orchestrator_model,
        tools=[*query_tools, AgentTool(command_pipeline), preload_memory_tool],
    )


def create_agents(
    model: object,
    create_cultivation_group,
    create_gardener_group,
    create_storekeeper_group,
    create_sensei_group,
):
    botanist, kikaru = create_cultivation_group(model=model)
    nursery, caretaker, gallery = create_gardener_group(model=model)
    storekeeper = create_storekeeper_group(model=model)

    return create_sensei_group(
        model=model,
        command_agents=[
            botanist,
            kikaru,
            nursery,
            caretaker,
            gallery,
            storekeeper,
        ],
    )
