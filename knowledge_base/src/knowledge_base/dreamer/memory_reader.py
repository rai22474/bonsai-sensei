import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

_SYNC_FILE_NAME = "memory-sync.json"
_LOCAL_OBSERVATIONS_FILE = "pending-observations.jsonl"
_ADMIN_CORRECTIONS_FILE = "pending-corrections.jsonl"
_DEFAULT_START = datetime(2024, 1, 1, tzinfo=timezone.utc)


async def read_new_observations(episodic_memory_url: str, wiki_root: Path) -> list[str]:
    """Read observations from the episodic memory service since the last dreamer run."""
    last_run = read_high_watermark(wiki_root)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{episodic_memory_url.rstrip('/')}/observations",
            params={"since": last_run.isoformat()},
            timeout=30,
        )
        response.raise_for_status()
    return response.json().get("observations", [])


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
