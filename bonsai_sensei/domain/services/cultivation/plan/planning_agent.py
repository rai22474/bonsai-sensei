from typing import Callable

from google.adk.agents.llm_agent import Agent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.tools import AgentTool

from bonsai_sensei.domain.services.cultivation.plan.kikaku import create_kikaku
from bonsai_sensei.domain.services.cultivation.plan.seko import create_seko


def _build_action_descriptions(advisors: list[Agent], tools: list[Callable]) -> list[str]:
    agent_lines = [f"- {advisor.name}: {advisor.description}" for advisor in advisors]
    tool_lines = [
        f"- {tool.__name__}: {(tool.__doc__ or '').strip().splitlines()[0]}"
        for tool in tools
    ]
    return agent_lines + tool_lines


def create_planning_agent(
    model: object,
    orchestrator_model: object,
    fertilizer_advisor: Agent,
    phytosanitary_advisor: Agent,
    list_planned_works_tool: Callable | None = None,
    list_bonsai_events_tool: Callable | None = None,
    create_fertilizer_application_tool: Callable | None = None,
    create_phytosanitary_application_tool: Callable | None = None,
    create_transplant_tool: Callable | None = None,
    delete_planned_work_tool: Callable | None = None,
    list_collection_tool: Callable | None = None,
    list_weekend_planned_works_tool: Callable | None = None,
) -> SequentialAgent:
    direct_tools = [
        tool
        for tool in [
            list_planned_works_tool,
            list_bonsai_events_tool,
            create_fertilizer_application_tool,
            create_phytosanitary_application_tool,
            create_transplant_tool,
            delete_planned_work_tool,
            list_collection_tool,
            list_weekend_planned_works_tool,
        ]
        if tool is not None
    ]

    advisors = [fertilizer_advisor, phytosanitary_advisor]
    available_actions = _build_action_descriptions(advisors=advisors, tools=direct_tools)

    kikaku = create_kikaku(
        model=orchestrator_model,
        available_actions=available_actions,
    )
    seko = create_seko(
        model=model,
        tools=[
            AgentTool(fertilizer_advisor),
            AgentTool(phytosanitary_advisor),
            *direct_tools,
        ],
    )

    return SequentialAgent(
        name="planning_agent",
        description="Gestiona el plan de trabajos de cultivo: crea, lista y consulta fertilizaciones, trasplantes y tratamientos fitosanitarios. Decide la fecha por defecto (próximo sábado) cuando el usuario no especifica una.",
        sub_agents=[kikaku, seko],
    )
