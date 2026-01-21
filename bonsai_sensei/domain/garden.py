from typing import List
from sqlmodel import select, Session
from bonsai_sensei.database import Species
from bonsai_sensei.database.session_wrapper import with_session


@with_session
def get_all_species(session: Session) -> List[str]:
    statement = select(Species.name)
    results = session.exec(statement).all()
    
    return sorted(list(set(results)))


@with_session
def list_species(session: Session) -> List[Species]:
    statement = select(Species)
    return session.exec(statement).all()


@with_session
def create_species(session: Session, species: Species) -> Species:
    session.add(species)
    return species


@with_session
def update_species(session: Session, species_id: int, species_data: dict) -> Species | None:
    species = session.get(Species, species_id)
    if not species:
        return None
    
    for key, value in species_data.items():
        if value is not None:
            setattr(species, key, value)
    
    session.add(species)
    return species


@with_session
def delete_species(session: Session, species_id: int) -> bool:
    species = session.get(Species, species_id)
    if not species:
        return False
    session.delete(species)
    return True