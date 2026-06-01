import json
from pathlib import Path

from knowledge_base.wiki_review_session import WikiReviewSession

_CONFIG_FILENAME = ".admin_config.json"
_REVIEW_SESSIONS_FILENAME = ".review_sessions.json"


def _config_path(wiki_root: Path) -> Path:
    return wiki_root / _CONFIG_FILENAME


def _sessions_path(wiki_root: Path) -> Path:
    return wiki_root / _REVIEW_SESSIONS_FILENAME


def load_admin_chat_id(wiki_root: Path) -> str | None:
    path = _config_path(wiki_root)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return data.get("admin_chat_id")


def save_admin_chat_id(wiki_root: Path, chat_id: str) -> None:
    path = _config_path(wiki_root)
    path.write_text(json.dumps({"admin_chat_id": chat_id}))


def load_review_sessions(wiki_root: Path) -> dict[str, WikiReviewSession]:
    path = _sessions_path(wiki_root)
    if not path.exists():
        return {}
    raw = json.loads(path.read_text())
    sessions = {}
    for review_id, data in raw.items():
        data["pending"] = [p for p in data.get("pending", []) if p.endswith(".md")]
        if data["pending"]:
            sessions[review_id] = WikiReviewSession(**data)
    return sessions


def save_review_sessions(wiki_root: Path, sessions: dict[str, WikiReviewSession]) -> None:
    path = _sessions_path(wiki_root)
    raw = {
        review_id: {
            "review_id": session.review_id,
            "commit_hash": session.commit_hash,
            "pending": session.pending,
            "confirmed": session.confirmed,
            "reverted": session.reverted,
        }
        for review_id, session in sessions.items()
    }
    path.write_text(json.dumps(raw))
