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
    statement = select(Phytosanitary).where(Phytosanitary.name == name)
    return session.exec(statement).first()


@with_session
def create_phytosanitary(
    session: Session,
    phytosanitary: Phytosanitary,
) -> Phytosanitary:
    session.add(phytosanitary)
    return phytosanitary
