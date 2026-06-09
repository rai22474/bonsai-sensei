import uuid
from collections.abc import AsyncGenerator, Callable, Sequence

from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner, RunConfig
from google.genai import types


def create_single_turn_llm_runner(
    model: object,
    app_name: str,
    instruction: str,
    tools: Sequence[Callable] = (),
    max_llm_calls: int = 10,
) -> Callable[[types.Content], AsyncGenerator]:
    agent = Agent(model=model, name=app_name, instruction=instruction, tools=list(tools))
    runner = InMemoryRunner(agent=agent, app_name=app_name)

    async def run(message: types.Content) -> AsyncGenerator:
        session_id = str(uuid.uuid4())
        await runner.session_service.create_session(
            app_name=app_name, user_id=app_name, session_id=session_id
        )
        async for event in runner.run_async(
            user_id=app_name,
            session_id=session_id,
            new_message=message,
            run_config=RunConfig(max_llm_calls=max_llm_calls),
        ):
            yield event

    return run
