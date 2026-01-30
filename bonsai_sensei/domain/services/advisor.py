from typing import Callable
from functools import partial
from google.adk.runners import InMemoryRunner

def create_advisor(sensei_agent) -> Callable[..., str]:
    runner = InMemoryRunner(agent=sensei_agent, app_name="bonsai_sensei")

    return partial(_generate_advise, runner=runner)


async def _generate_advise(
    text: str,
    runner: InMemoryRunner,
    user_id: str = "default_user",
) -> str:
    events = await runner.run_debug(
        user_messages=text,
        user_id=user_id,
        session_id=str(user_id),
        quiet=True,
    )
    response_texts = []
    for event in events:
        if event.content and hasattr(event.content, "parts") and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    response_texts.append(part.text)
    if not response_texts:
        return "No pude generar una respuesta en este momento."
    return "\n".join(response_texts)
