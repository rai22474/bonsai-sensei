import json
from datetime import datetime, timezone
from pathlib import Path

_SYNC_FILE_NAME = "memory-sync.json"
_PROCESSED_SESSIONS_FILE = "dreamer-processed-sessions.json"
_LOCAL_OBSERVATIONS_FILE = "pending-observations.json"
_DEFAULT_START = datetime(2024, 1, 1, tzinfo=timezone.utc)


async def read_new_observations(honcho_client, workspace_id: str, wiki_root: Path) -> list[str]:
    """Read observations from Honcho sessions not yet processed by the dreamer.

    Lists all sessions in the workspace, skips already-processed ones,
    extracts conclusions from new sessions, and saves their IDs.
    workspace_id is unused — the client already knows its workspace.
    """
    processed_ids = _read_processed_session_ids(wiki_root)
    sessions_page = await honcho_client.sessions()
    new_session_ids = []
    observations = []

    async for session in sessions_page:
        if session.id in processed_ids:
            continue
        new_session_ids.append(session.id)
        peers = await session.aio.peers()
        for peer in peers:
            conclusions_page = await peer.conclusions.aio.list(session=session)
            async for conclusion in conclusions_page:
                if conclusion.content:
                    observations.append(conclusion.content)

    if new_session_ids:
        _save_processed_session_ids(wiki_root, processed_ids | set(new_session_ids))

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
    """Clear the processed sessions log. Used in acceptance tests."""
    sessions_file = wiki_root / _PROCESSED_SESSIONS_FILE
    sessions_file.unlink(missing_ok=True)


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


def _read_processed_session_ids(wiki_root: Path) -> set[str]:
    sessions_file = wiki_root / _PROCESSED_SESSIONS_FILE
    if not sessions_file.exists():
        return set()
    return set(json.loads(sessions_file.read_text()))


def _save_processed_session_ids(wiki_root: Path, session_ids: set[str]) -> None:
    sessions_file = wiki_root / _PROCESSED_SESSIONS_FILE
    sessions_file.write_text(json.dumps(list(session_ids)))
