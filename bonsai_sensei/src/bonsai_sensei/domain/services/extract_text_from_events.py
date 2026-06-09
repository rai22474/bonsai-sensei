from typing import AsyncIterator


async def extract_text_from_events(events: AsyncIterator) -> str:
    """Collect and join all text parts from an ADK runner event stream."""
    parts = []
    async for event in events:
        if event.content and hasattr(event.content, "parts"):
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    parts.append(part.text)
    return "\n".join(parts)
