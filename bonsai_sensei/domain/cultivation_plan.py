from datetime import date
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
def list_planned_works_in_date_range(
    session: Session, start_date: date, end_date: date
) -> List[PlannedWork]:
    statement = (
        select(PlannedWork)
        .where(PlannedWork.scheduled_date >= start_date)
        .where(PlannedWork.scheduled_date <= end_date)
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


@with_session
def delete_future_planned_works_by_plan(session: Session, plan_id: int, cutoff_date: date) -> int:
    statement = (
        select(PlannedWork)
        .where(PlannedWork.plan_id == plan_id)
        .where(PlannedWork.scheduled_date > cutoff_date)
    )
    works = session.exec(statement).all()
    for work in works:
        session.delete(work)
    return len(works)
