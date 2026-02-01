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
    statement = select(Fertilizer).where(Fertilizer.name == name)
    return session.exec(statement).first()


@with_session
def create_fertilizer(session: Session, fertilizer: Fertilizer) -> Fertilizer:
    session.add(fertilizer)
    return fertilizer
