from typing import List
from sqlmodel import select, Session
from bonsai_sensei.database.bonsai import Bonsai
from bonsai_sensei.database.species import Species
from bonsai_sensei.database.session_wrapper import with_session


@with_session
def list_bonsai(session: Session) -> List[Bonsai]:
    statement = select(Bonsai)
    return session.exec(statement).all()


@with_session
def get_bonsai_by_name(session: Session, name: str) -> Bonsai | None:
    if not name:
        return None
    statement = select(Bonsai).where(Bonsai.name == name)
    return session.exec(statement).first()


@with_session
def create_bonsai(session: Session, bonsai: Bonsai) -> Bonsai | None:
    species = session.get(Species, bonsai.species_id)
    if not species:
        return None
    session.add(bonsai)
    return bonsai


@with_session
def update_bonsai(session: Session, bonsai_id: int, bonsai_data: dict) -> Bonsai | None:
    bonsai = session.get(Bonsai, bonsai_id)
    if not bonsai:
        return None
    species_id = bonsai_data.get("species_id") if bonsai_data else None
    if species_id is not None:
        species = session.get(Species, species_id)
        if not species:
            return None
    for key, value in (bonsai_data or {}).items():
        if value is not None:
            setattr(bonsai, key, value)
    session.add(bonsai)
    return bonsai


@with_session
def delete_bonsai(session: Session, bonsai_id: int) -> bool:
    bonsai = session.get(Bonsai, bonsai_id)
    if not bonsai:
        return False
    session.delete(bonsai)
    return True