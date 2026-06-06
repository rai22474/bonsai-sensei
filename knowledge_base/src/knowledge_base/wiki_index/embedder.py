import asyncio
from typing import Callable

from fastembed import TextEmbedding

_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIM = 384


def create_embed_text() -> Callable:
    """Create an async callable that generates text embeddings using a local model."""
    model = TextEmbedding(_EMBEDDING_MODEL)

    async def embed_text(text: str) -> list[float]:
        """Generate a text embedding using the local multilingual model."""
        embeddings = await asyncio.to_thread(lambda: list(model.embed([text])))
        return embeddings[0].tolist()

    return embed_text
