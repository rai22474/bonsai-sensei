from typing import Callable

import google.genai as genai

_EMBEDDING_MODEL = "models/gemini-embedding-001"


def create_embed_text(api_key: str) -> Callable:
    """Create an async callable that generates text embeddings using Gemini embedding model."""
    client = genai.Client(api_key=api_key)

    async def embed_text(text: str) -> list[float]:
        """Generate a text embedding using Gemini embedding model."""
        response = await client.aio.models.embed_content(model=_EMBEDDING_MODEL, contents=text)
        return response.embeddings[0].values

    return embed_text
