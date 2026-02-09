from typing import List
from sqlmodel import select, Session
from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.database.session_wrapper import with_session


@with_session
def list_fertilizers(session: Session) -> List[Fertilizer]:
    statement = select(Fertilizer)
    return session.exec(statement).all()


@with_session
def get_fertilizer_by_name(session: Session, name: str) -> Fertilizer | None:
    if not name:
        return None
    return _find_fertilizer_by_name(session, name)


@with_session
def create_fertilizer(session: Session, fertilizer: Fertilizer) -> Fertilizer:
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
def delete_fertilizer(session: Session, name: str) -> bool:
    if not name:
        return False
    fertilizer = _find_fertilizer_by_name(session, name)
    if not fertilizer:
        return False
    session.delete(fertilizer)
    return True


def _find_fertilizer_by_name(
    session: Session,
    name: str,
) -> Fertilizer | None:
    statement = select(Fertilizer).where(Fertilizer.name == name)
    return session.exec(statement).first()
