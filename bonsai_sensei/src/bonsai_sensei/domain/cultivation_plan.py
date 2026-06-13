from datetime import date, datetime, timedelta, timezone
from typing import List
from sqlmodel import select, Session

from bonsai_sensei.domain.planned_work import PlannedWork, PlannedWorkPhoto
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
    session: Session, start_date: date, end_date: date, bonsai_id: int | None = None
) -> List[PlannedWork]:
    statement = (
        select(PlannedWork)
        .where(PlannedWork.scheduled_date >= start_date)
        .where(PlannedWork.scheduled_date <= end_date)
        .order_by(PlannedWork.scheduled_date)
    )
    if bonsai_id is not None:
        statement = statement.where(PlannedWork.bonsai_id == bonsai_id)
    return session.exec(statement).all()


@with_session
def get_planned_work(session: Session, work_id: int) -> PlannedWork | None:
    return session.get(PlannedWork, work_id)


@with_session
def create_planned_work(session: Session, planned_work: PlannedWork) -> PlannedWork:
    session.add(planned_work)
    return planned_work


@with_session
def update_planned_work_wiki_paths(
    session: Session,
    work_id: int,
    refinement_wiki_path: str | None = None,
    result_wiki_path: str | None = None,
) -> PlannedWork | None:
    work = session.get(PlannedWork, work_id)
    if not work:
        return None
    if refinement_wiki_path is not None:
        work.refinement_wiki_path = refinement_wiki_path
    if result_wiki_path is not None:
        work.result_wiki_path = result_wiki_path
    session.add(work)
    return work


@with_session
def delete_planned_work(session: Session, work_id: int) -> bool:
    planned_work = session.get(PlannedWork, work_id)
    if not planned_work:
        return False
    session.delete(planned_work)
    return True


@with_session
def delete_future_planned_works_by_phytosanitary_plan(session: Session, plan_id: int, cutoff_date: date) -> int:
    statement = (
        select(PlannedWork)
        .where(PlannedWork.phytosanitary_plan_id == plan_id)
        .where(PlannedWork.scheduled_date > cutoff_date)
    )
    works = session.exec(statement).all()
    for work in works:
        session.delete(work)
    return len(works)


@with_session
def delete_future_planned_works_by_development_plan(session: Session, plan_id: int, cutoff_date: date) -> int:
    statement = (
        select(PlannedWork)
        .where(PlannedWork.development_plan_id == plan_id)
        .where(PlannedWork.scheduled_date > cutoff_date)
    )
    works = session.exec(statement).all()
    for work in works:
        session.delete(work)
    return len(works)


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


@with_session
def link_recent_photos_to_work(session: Session, bonsai_id: int, planned_work_id: int, hours: int = 24) -> int:
    from bonsai_sensei.domain.bonsai_photo import BonsaiPhoto
    cutoff_date = (datetime.now(timezone.utc) - timedelta(hours=hours)).date()
    already_linked_ids = set(session.exec(
        select(PlannedWorkPhoto.photo_id).where(PlannedWorkPhoto.planned_work_id == planned_work_id)
    ).all())
    photos = session.exec(
        select(BonsaiPhoto)
        .where(BonsaiPhoto.bonsai_id == bonsai_id)
        .where(BonsaiPhoto.taken_on >= cutoff_date)
    ).all()
    new_links = [photo for photo in photos if photo.id not in already_linked_ids]
    for photo in new_links:
        session.add(PlannedWorkPhoto(planned_work_id=planned_work_id, photo_id=photo.id))
    return len(new_links)
