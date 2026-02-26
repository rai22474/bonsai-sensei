from typing import List
from sqlmodel import select, Session

from bonsai_sensei.domain.planned_work import PlannedWork
from bonsai_sensei.database.session_wrapper import with_session


@with_session
def list_planned_works(session: Session, bonsai_id: int) -> List[PlannedWork]:
    statement = (
        select(PlannedWork)
        .where(PlannedWork.bonsai_id == bonsai_id)
        .order_by(PlannedWork.scheduled_date)
    )
    return session.exec(statement).all()


@with_session
def get_planned_work(session: Session, work_id: int) -> PlannedWork | None:
    return session.get(PlannedWork, work_id)


@with_session
def create_planned_work(session: Session, planned_work: PlannedWork) -> PlannedWork:
    session.add(planned_work)
    return planned_work


@with_session
def delete_planned_work(session: Session, work_id: int) -> bool:
    planned_work = session.get(PlannedWork, work_id)
    if not planned_work:
        return False
    session.delete(planned_work)
    return True
