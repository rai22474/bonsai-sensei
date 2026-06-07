from typing import List
from sqlmodel import select, Session
from sqlalchemy import func
from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.database.session_wrapper import with_session


@with_session
def list_fertilizers(session: Session, user_id: str | None = None) -> List[Fertilizer]:
    statement = select(Fertilizer)
    if user_id is not None:
        statement = statement.where(Fertilizer.user_id == user_id)
    return session.exec(statement).all()


@with_session
def get_fertilizer_by_name(session: Session, name: str, user_id: str | None = None) -> Fertilizer | None:
    if not name:
        return None
    return _find_fertilizer_by_name(session, name, user_id)


@with_session
def create_fertilizer(session: Session, fertilizer: Fertilizer) -> Fertilizer:
    fertilizer.name = fertilizer.name.lower()
    session.add(fertilizer)
    return fertilizer


@with_session
def update_fertilizer(
    session: Session,
    name: str,
    fertilizer_data: dict,
) -> Fertilizer | None:
    if not name:
        return None
    fertilizer = _find_fertilizer_by_name(session, name)
    if not fertilizer:
        return None
    for key, value in fertilizer_data.items():
        if value is not None:
            setattr(fertilizer, key, value)
    session.add(fertilizer)
    return fertilizer


@with_session
def delete_fertilizer(session: Session, name: str, user_id: str | None = None) -> bool:
    if not name:
        return False
    fertilizer = _find_fertilizer_by_name(session, name, user_id)
    if not fertilizer:
        return False
    session.delete(fertilizer)
    return True


def _find_fertilizer_by_name(
    session: Session,
    name: str,
    user_id: str | None = None,
) -> Fertilizer | None:
    statement = select(Fertilizer).where(func.lower(Fertilizer.name) == name.lower())
    if user_id is not None:
        statement = statement.where(Fertilizer.user_id == user_id)
    return session.exec(statement).first()
