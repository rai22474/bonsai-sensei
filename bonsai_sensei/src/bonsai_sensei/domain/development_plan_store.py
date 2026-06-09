from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlmodel import Session, select

from bonsai_sensei.database.session_wrapper import with_session
from bonsai_sensei.domain.development_plan import DevelopmentPlan


@with_session
def get_active_development_plan(session: Session, bonsai_id: int) -> Optional[DevelopmentPlan]:
    statement = (
        select(DevelopmentPlan)
        .where(DevelopmentPlan.bonsai_id == bonsai_id)
        .where(DevelopmentPlan.status == "active")
    )
    return session.exec(statement).first()


@with_session
def list_development_plans(session: Session, bonsai_id: int) -> List[DevelopmentPlan]:
    statement = (
        select(DevelopmentPlan)
        .where(DevelopmentPlan.bonsai_id == bonsai_id)
        .order_by(DevelopmentPlan.created_at)
    )
    return session.exec(statement).all()


@with_session
def get_development_plan(session: Session, plan_id: int) -> Optional[DevelopmentPlan]:
    return session.get(DevelopmentPlan, plan_id)


@with_session
def create_development_plan(session: Session, plan: DevelopmentPlan) -> DevelopmentPlan:
    session.add(plan)
    return plan


@with_session
def update_development_plan(session: Session, plan: DevelopmentPlan) -> DevelopmentPlan:
    db_plan = session.get(DevelopmentPlan, plan.id)
    if not db_plan:
        return plan
    db_plan.status = plan.status
    db_plan.abandonment_reason = plan.abandonment_reason
    db_plan.abandoned_at = plan.abandoned_at
    db_plan.wiki_path = plan.wiki_path
    db_plan.current_phase = plan.current_phase
    session.add(db_plan)
    return db_plan


@with_session
def get_recently_abandoned_development_plans(
    session: Session,
    bonsai_id: int,
    days: int = 90,
    reason_contains: str = "disease_pause",
) -> List[DevelopmentPlan]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    statement = (
        select(DevelopmentPlan)
        .where(DevelopmentPlan.bonsai_id == bonsai_id)
        .where(DevelopmentPlan.status == "abandoned")
        .where(DevelopmentPlan.abandoned_at >= cutoff)
        .where(DevelopmentPlan.abandonment_reason.like(f"%{reason_contains}%"))
    )
    return session.exec(statement).all()


@with_session
def delete_development_plan(session: Session, plan_id: int) -> bool:
    plan = session.get(DevelopmentPlan, plan_id)
    if not plan:
        return False
    session.delete(plan)
    return True
