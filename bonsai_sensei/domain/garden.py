from typing import List, Dict
from sqlmodel import select, Session
from bonsai_sensei.database import Species
from bonsai_sensei.database.session_wrapper import with_session


@with_session
def get_all_species(session: Session) -> List[Dict[str, str]]:
    statement = select(Species)
    results = session.exec(statement).all()

    species_items = []
    for species in results:
        species_items.append(
            {
                "common_name": species.name,
                "scientific_name": species.scientific_name or "",
            }
        )

    return sorted(species_items, key=lambda item: item["common_name"])


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