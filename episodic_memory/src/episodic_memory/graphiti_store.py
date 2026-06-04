import logging
import time
import uuid
from datetime import datetime, timezone

from graphiti_core import Graphiti
from graphiti_core.cross_encoder.gemini_reranker_client import GeminiRerankerClient
from graphiti_core.driver.falkordb_driver import FalkorDriver
from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.llm_client.gemini_client import GeminiClient
from graphiti_core.nodes import EpisodeType

logger = logging.getLogger(__name__)

from episodic_memory.metrics import (
    EPISODE_DURATION_SECONDS,
    EPISODES_TOTAL,
    OBSERVATIONS_RETURNED_TOTAL,
    SEARCH_REQUESTS_TOTAL,
)


class GraphitiStore:
    def __init__(self, graphiti: Graphiti):
        self._graphiti = graphiti

    async def initialize(self) -> None:
        """Build indices and constraints on startup."""
        await self._graphiti.build_indices_and_constraints()

    async def add_episode(self, user_id: str, messages: list[dict]) -> None:
        """Ingest a conversation as a Graphiti episode.

        Formats messages as 'role: content' lines so the LLM can extract
        entities and facts from the full conversation turn sequence.
        """
        episode_body = "\n".join(f"{message['role']}: {message['content']}" for message in messages)
        start = time.perf_counter()
        status = "success"
        try:
            await self._graphiti.add_episode(
                name=str(uuid.uuid4()),
                episode_body=episode_body,
                source_description="bonsai sensei conversation",
                reference_time=datetime.now(timezone.utc),
                source=EpisodeType.message,
                group_id=user_id,
            )
        except Exception:
            status = "error"
            raise
        finally:
            EPISODE_DURATION_SECONDS.observe(time.perf_counter() - start)
            EPISODES_TOTAL.labels(status=status).inc()

    async def search(self, user_id: str, query: str) -> list[str]:
        """Return relevant facts for a user, filtered by group_id."""
        status = "success"
        try:
            edges = await self._graphiti.search(query, group_ids=[user_id])
            return [edge.fact for edge in edges if edge.fact]
        except Exception:
            status = "error"
            raise
        finally:
            SEARCH_REQUESTS_TOTAL.labels(status=status).inc()

    async def get_new_episodes(self, since: datetime) -> list[str]:
        """Return episode content for all users with valid_at > since."""
        episodes = await self._graphiti.retrieve_episodes(
            reference_time=datetime.now(timezone.utc),
            last_n=500,
        )
        logger.info("retrieve_episodes returned %d episodes, filtering since=%s", len(episodes), since)
        for episode in episodes:
            valid_at = episode.valid_at
            if valid_at.tzinfo is None:
                valid_at = valid_at.replace(tzinfo=timezone.utc)
            logger.debug("episode uuid=%s valid_at=%s content_len=%d", episode.uuid, valid_at, len(episode.content or ""))
        since_aware = since if since.tzinfo is not None else since.replace(tzinfo=timezone.utc)
        observations = [
            episode.content
            for episode in episodes
            if episode.content and (episode.valid_at.replace(tzinfo=timezone.utc) if episode.valid_at.tzinfo is None else episode.valid_at) > since_aware
        ]
        logger.info("Returning %d observations (since=%s)", len(observations), since_aware)
        OBSERVATIONS_RETURNED_TOTAL.inc(len(observations))
        return observations

    async def close(self) -> None:
        await self._graphiti.close()


def create_graphiti_store(host: str, port: int, gemini_api_key: str, model: str) -> GraphitiStore:
    """Create a GraphitiStore backed by FalkorDB and Gemini."""
    driver = FalkorDriver(host=host, port=port)
    llm_config = LLMConfig(api_key=gemini_api_key, model=model)
    llm_client = GeminiClient(config=llm_config)
    embedder = GeminiEmbedder(config=GeminiEmbedderConfig(api_key=gemini_api_key, embedding_model="gemini-embedding-001"))
    cross_encoder = GeminiRerankerClient(config=llm_config)
    graphiti = Graphiti(graph_driver=driver, llm_client=llm_client, embedder=embedder, cross_encoder=cross_encoder)
    return GraphitiStore(graphiti)
