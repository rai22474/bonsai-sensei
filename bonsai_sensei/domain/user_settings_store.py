from sqlmodel import select, Session
from bonsai_sensei.domain.user_settings import UserSettings
from bonsai_sensei.database.session_wrapper import with_session


@with_session
def save_user_settings(session: Session, user_settings: UserSettings) -> UserSettings:
    existing = session.get(UserSettings, user_settings.user_id)
    if existing:
        if user_settings.location is not None:
            existing.location = user_settings.location
        if user_settings.telegram_chat_id is not None:
            existing.telegram_chat_id = user_settings.telegram_chat_id
        session.add(existing)
        return existing
    session.add(user_settings)
    return user_settings


@with_session
def get_user_settings(session: Session, user_id: str) -> UserSettings | None:
    return session.get(UserSettings, user_id)


@with_session
def list_all_user_settings(session: Session) -> list[UserSettings]:
    return session.exec(select(UserSettings)).all()


@with_session
def delete_user_settings(session: Session, user_id: str) -> bool:
    user_settings = session.get(UserSettings, user_id)
    if not user_settings:
        return False
    session.delete(user_settings)
    return True
