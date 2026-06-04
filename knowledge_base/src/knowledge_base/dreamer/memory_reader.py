import json
from datetime import datetime, timezone
from pathlib import Path

_SYNC_FILE_NAME = "memory-sync.json"
_PROCESSED_CONCLUSIONS_FILE = "dreamer-processed-conclusions.json"
_LOCAL_OBSERVATIONS_FILE = "pending-observations.jsonl"
_ADMIN_CORRECTIONS_FILE = "pending-corrections.jsonl"
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
    """Read and consume all observations from the local pending-observations.jsonl queue."""
    observations_file = wiki_root / _LOCAL_OBSERVATIONS_FILE
    if not observations_file.exists():
        return []
    lines = [line.strip() for line in observations_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    observations_file.unlink()
    return [json.loads(line) for line in lines]


def append_local_observation(wiki_root: Path, text: str) -> None:
    """Append an observation to the local pending-observations.jsonl queue (true append, no read-modify-write)."""
    observations_file = wiki_root / _LOCAL_OBSERVATIONS_FILE
    with observations_file.open("a", encoding="utf-8") as file:
        file.write(json.dumps(text) + "\n")


def read_admin_corrections(wiki_root: Path) -> list[str]:
    """Read and consume all admin corrections from the pending-corrections.jsonl queue."""
    corrections_file = wiki_root / _ADMIN_CORRECTIONS_FILE
    if not corrections_file.exists():
        return []
    lines = [line.strip() for line in corrections_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    corrections_file.unlink()
    return [json.loads(line) for line in lines]


def append_admin_correction(wiki_root: Path, text: str) -> None:
    """Append an admin correction to the pending-corrections.jsonl queue."""
    corrections_file = wiki_root / _ADMIN_CORRECTIONS_FILE
    with corrections_file.open("a", encoding="utf-8") as file:
        file.write(json.dumps(text) + "\n")


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
