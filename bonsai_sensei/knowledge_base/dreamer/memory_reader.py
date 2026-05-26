import json
from datetime import datetime, timezone
from pathlib import Path

from mem0 import AsyncMemory

_SYNC_FILE_NAME = "memory-sync.json"
_DEFAULT_START = datetime(2024, 1, 1, tzinfo=timezone.utc)


_AGENT_ID = "bonsai_sensei"


async def read_new_observations(mem0_client: AsyncMemory, wiki_root: Path) -> list[str]:
    """Reads episodic observations captured since the last keeper run."""
    last_run = read_high_watermark(wiki_root)
    results = await mem0_client.get_all(filters={"agent_id": _AGENT_ID})
    all_memories = results.get("results", [])
    new_memories = [
        memory["memory"]
        for memory in all_memories
        if _parse_created_at(memory.get("created_at")) >= last_run
    ]
    return new_memories


def _parse_created_at(value: str | None) -> datetime:
    if not value:
        return _DEFAULT_START
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def update_high_watermark(wiki_root: Path) -> None:
    """Persists the current timestamp as the high-watermark for the next keeper run."""
    sync_file = wiki_root / _SYNC_FILE_NAME
    sync_file.write_text(
        json.dumps({"last_processed_at": datetime.now(timezone.utc).isoformat()})
    )


def read_high_watermark(wiki_root: Path) -> datetime:
    sync_file = wiki_root / _SYNC_FILE_NAME
    if not sync_file.exists():
        return _DEFAULT_START
    data = json.loads(sync_file.read_text())
    return datetime.fromisoformat(data["last_processed_at"])
