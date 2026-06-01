from typing import List
from sqlalchemy import func
from sqlmodel import select, Session
from bonsai_sensei.domain.pest import Pest
from bonsai_sensei.database.session_wrapper import with_session


@with_session
def list_pests(session: Session) -> List[Pest]:
    return session.exec(select(Pest)).all()


@with_session
def get_pest_by_name(session: Session, name: str) -> Pest | None:
    if not name:
        return None
    return _find_pest_by_name(session, name)


@with_session
def create_pest(session: Session, pest: Pest) -> Pest:
    pest.name = pest.name.lower()
    session.add(pest)
    return pest


@with_session
def delete_pest(session: Session, name: str) -> bool:
    if not name:
        return False
    pest = _find_pest_by_name(session, name)
    if not pest:
        return False
    session.delete(pest)
    return True


def _find_pest_by_name(session: Session, name: str) -> Pest | None:
    statement = select(Pest).where(func.lower(Pest.name) == name.lower())
    return session.exec(statement).first()
