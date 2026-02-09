from typing import List
from sqlmodel import select, Session
from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.database.session_wrapper import with_session


@with_session
def list_phytosanitary(session: Session) -> List[Phytosanitary]:
    statement = select(Phytosanitary)
    return session.exec(statement).all()


@with_session
def get_phytosanitary_by_name(session: Session, name: str) -> Phytosanitary | None:
    if not name:
        return None
    return _find_phytosanitary_by_name(session, name)


@with_session
def create_phytosanitary(
    session: Session,
    phytosanitary: Phytosanitary,
) -> Phytosanitary:
    session.add(phytosanitary)
    return phytosanitary


@with_session
def update_phytosanitary(
    session: Session,
    name: str,
    phytosanitary_data: dict,
) -> Phytosanitary | None:
    if not name:
        return None
    phytosanitary = _find_phytosanitary_by_name(session, name)
    if not phytosanitary:
        return None
    for key, value in phytosanitary_data.items():
        if value is not None:
            setattr(phytosanitary, key, value)
    session.add(phytosanitary)
    return phytosanitary


@with_session
def delete_phytosanitary(session: Session, name: str) -> bool:
    if not name:
        return False
    phytosanitary = _find_phytosanitary_by_name(session, name)
    if not phytosanitary:
        return False
    session.delete(phytosanitary)
    return True


def _find_phytosanitary_by_name(
    session: Session,
    name: str,
) -> Phytosanitary | None:
    statement = select(Phytosanitary).where(Phytosanitary.name == name)
    return session.exec(statement).first()
