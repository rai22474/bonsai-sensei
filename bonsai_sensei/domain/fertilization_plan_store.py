from typing import List, Optional

from sqlmodel import Session, select

from bonsai_sensei.database.session_wrapper import with_session
from bonsai_sensei.domain.fertilization_plan import FertilizationPlan


@with_session
def get_active_fertilization_plan(session: Session, bonsai_id: int) -> Optional[FertilizationPlan]:
    statement = (
        select(FertilizationPlan)
        .where(FertilizationPlan.bonsai_id == bonsai_id)
        .where(FertilizationPlan.status == "active")
    )
    return session.exec(statement).first()


@with_session
def list_fertilization_plans(session: Session, bonsai_id: int) -> List[FertilizationPlan]:
    statement = (
        select(FertilizationPlan)
        .where(FertilizationPlan.bonsai_id == bonsai_id)
        .order_by(FertilizationPlan.created_at)
    )
    return session.exec(statement).all()


@with_session
def get_fertilization_plan(session: Session, plan_id: int) -> Optional[FertilizationPlan]:
    return session.get(FertilizationPlan, plan_id)


@with_session
def create_fertilization_plan(session: Session, plan: FertilizationPlan) -> FertilizationPlan:
    session.add(plan)
    return plan


@with_session
def update_fertilization_plan(session: Session, plan: FertilizationPlan) -> FertilizationPlan:
    db_plan = session.get(FertilizationPlan, plan.id)
    if not db_plan:
        return plan
    db_plan.status = plan.status
    db_plan.abandonment_reason = plan.abandonment_reason
    db_plan.abandoned_at = plan.abandoned_at
    db_plan.wiki_path = plan.wiki_path
    session.add(db_plan)
    return db_plan


@with_session
def delete_fertilization_plan(session: Session, plan_id: int) -> bool:
    plan = session.get(FertilizationPlan, plan_id)
    if not plan:
        return False
    session.delete(plan)
    return True
