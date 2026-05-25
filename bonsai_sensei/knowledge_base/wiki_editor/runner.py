import uuid
from pathlib import Path
from typing import Callable, Optional

from google.adk.runners import InMemoryRunner, RunConfig
from google.genai import types

from bonsai_sensei.knowledge_base import wiki_git
from bonsai_sensei.knowledge_base.wiki_editor.agent import _APP_NAME, create_wiki_editor_agent
from bonsai_sensei.knowledge_base.wiki_index.indexer import update_page_index
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)

_MAX_LLM_CALLS = 80


def create_wiki_editor(
    model: object,
    wiki_root: Path,
    notify_admin: Optional[Callable] = None,
    embed: Optional[Callable] = None,
) -> Callable:
    """Creates the wiki editor runner, a conversational agent for admin wiki management.

    Manages one ADK session per admin chat_id. After each interaction, commits any
    changed wiki files and calls notify_admin(changed_files, commit_hash) if provided.

    Returns:
        Async callable: (chat_id: str, text: str) -> str (agent response text)
    """
    wiki_git.init_wiki_repo(wiki_root)
    agent = create_wiki_editor_agent(model, wiki_root)
    runner = InMemoryRunner(agent=agent, app_name=_APP_NAME)
    chat_id_to_session_id: dict[str, str] = {}

    async def run_wiki_editor(chat_id: str, text: str) -> str:
        session_id = await _get_or_create_session(runner, chat_id, chat_id_to_session_id)

        message = types.Content(role="user", parts=[types.Part(text=text)])
        last_text = ""
        async for event in runner.run_async(
            user_id=chat_id,
            session_id=session_id,
            new_message=message,
            run_config=RunConfig(max_llm_calls=_MAX_LLM_CALLS),
        ):
            if event.author != "user" and event.content and event.content.parts:
                candidate_text = event.content.parts[0].text
                if candidate_text:
                    last_text = candidate_text

        commit_hash = wiki_git.commit_wiki_changes(wiki_root, "wiki-editor: admin update")
        if commit_hash:
            changed_files = wiki_git.get_changed_files(wiki_root, commit_hash)
            if changed_files and embed is not None:
                for file_path in changed_files:
                    if file_path.endswith(".md"):
                        await update_page_index(file_path, wiki_root, embed)
            if changed_files and notify_admin:
                await notify_admin(changed_files, commit_hash)

        return last_text

    return run_wiki_editor


async def _get_or_create_session(runner: InMemoryRunner, chat_id: str, chat_id_to_session_id: dict[str, str]) -> str:
    if chat_id not in chat_id_to_session_id:
        session_id = str(uuid.uuid4())
        await runner.session_service.create_session(app_name=_APP_NAME, user_id=chat_id, session_id=session_id)
        chat_id_to_session_id[chat_id] = session_id
    return chat_id_to_session_id[chat_id]
