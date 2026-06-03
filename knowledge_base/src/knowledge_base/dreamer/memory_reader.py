import json
from datetime import datetime, timezone
from pathlib import Path

_SYNC_FILE_NAME = "memory-sync.json"
_PROCESSED_CONCLUSIONS_FILE = "dreamer-processed-conclusions.json"
_LOCAL_OBSERVATIONS_FILE = "pending-observations.json"
_DEFAULT_START = datetime(2024, 1, 1, tzinfo=timezone.utc)


async def read_new_observations(honcho_client, workspace_id: str, wiki_root: Path) -> list[str]:
    """Read observations from Honcho peer conclusions not yet processed by the dreamer.

    Iterates all workspace peers directly (not sessions→peers, since peers are not
    registered as session members when messages are added via add_messages()).
    Tracks processed conclusion IDs to avoid re-reading.
    workspace_id is unused — the client already knows its workspace.
    """
    processed_ids = _read_processed_conclusion_ids(wiki_root)
    new_conclusion_ids = set()
    observations = []

    peers_page = await honcho_client.peers()
    async for peer in peers_page:
        conclusions_page = await peer.conclusions.aio.list()
        async for conclusion in conclusions_page:
            if not conclusion.content or conclusion.id in processed_ids:
                continue
            observations.append(conclusion.content)
            new_conclusion_ids.add(conclusion.id)

    if new_conclusion_ids:
        _save_processed_conclusion_ids(wiki_root, processed_ids | new_conclusion_ids)

    return observations


def read_local_observations(wiki_root: Path) -> list[str]:
    """Read observations from the local pending-observations.json file and clear it."""
    observations_file = wiki_root / _LOCAL_OBSERVATIONS_FILE
    if not observations_file.exists():
        return []
    observations = json.loads(observations_file.read_text())
    observations_file.unlink()
    return observations


def append_local_observation(wiki_root: Path, text: str) -> None:
    """Append an observation to the local pending-observations.json file."""
    observations_file = wiki_root / _LOCAL_OBSERVATIONS_FILE
    observations = json.loads(observations_file.read_text()) if observations_file.exists() else []
    observations.append(text)
    observations_file.write_text(json.dumps(observations))


def reset_processed_sessions(wiki_root: Path) -> None:
    """Clear the processed conclusions log. Used in acceptance tests."""
    conclusions_file = wiki_root / _PROCESSED_CONCLUSIONS_FILE
    conclusions_file.unlink(missing_ok=True)


def update_high_watermark(wiki_root: Path) -> None:
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


def _read_processed_conclusion_ids(wiki_root: Path) -> set[str]:
    conclusions_file = wiki_root / _PROCESSED_CONCLUSIONS_FILE
    if not conclusions_file.exists():
        return set()
    return set(json.loads(conclusions_file.read_text()))


def _save_processed_conclusion_ids(wiki_root: Path, conclusion_ids: set[str]) -> None:
    conclusions_file = wiki_root / _PROCESSED_CONCLUSIONS_FILE
    conclusions_file.write_text(json.dumps(list(conclusion_ids)))
