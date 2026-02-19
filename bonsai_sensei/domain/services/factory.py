from google.adk.tools import AgentTool

from bonsai_sensei.domain.services.sensei import create_sensei


def create_sensei_group(
    model: object,
    cultivation_agent,
    gardener_agent,
    storekeeper_agent,
):
    sensei_tools = [
        AgentTool(cultivation_agent),
        AgentTool(gardener_agent),
        AgentTool(storekeeper_agent),
    ]
    sensei_agent = create_sensei(
        model=model,
        tools=sensei_tools,
    )
    return sensei_agent


def create_agents(
    model: object,
    create_cultivation_group,
    create_gardener_group,
    create_storekeeper_group,
    create_sensei_group,
):
    cultivation_agent = create_cultivation_group(model=model)
    gardener_agent = create_gardener_group(model=model)
    storekeeper_agent = create_storekeeper_group(model=model)
    
    return create_sensei_group(
        model=model,
        cultivation_agent=cultivation_agent,
        gardener_agent=gardener_agent,
        storekeeper_agent=storekeeper_agent,
    )
