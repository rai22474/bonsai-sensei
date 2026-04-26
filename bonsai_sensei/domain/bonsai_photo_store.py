from typing import List
from sqlmodel import select, Session
from bonsai_sensei.domain.bonsai_photo import BonsaiPhoto
from bonsai_sensei.database.session_wrapper import with_session


@with_session
def create_bonsai_photo(session: Session, bonsai_photo: BonsaiPhoto) -> BonsaiPhoto:
    session.add(bonsai_photo)
    return bonsai_photo


@with_session
def list_bonsai_photos(session: Session, bonsai_id: int) -> List[BonsaiPhoto]:
    statement = select(BonsaiPhoto).where(BonsaiPhoto.bonsai_id == bonsai_id).order_by(BonsaiPhoto.taken_on)
    return session.exec(statement).all()


@with_session
def delete_bonsai_photos(session: Session, bonsai_id: int) -> None:
    photos = session.exec(select(BonsaiPhoto).where(BonsaiPhoto.bonsai_id == bonsai_id)).all()
    for photo in photos:
        session.delete(photo)
