from typing import List, Optional

from sqlmodel import Session, select

from bonsai_sensei.database.session_wrapper import with_session
from bonsai_sensei.domain.phytosanitary_plan import PhytosanitaryPlan


@with_session
def get_active_phytosanitary_plan(session: Session, bonsai_id: int) -> Optional[PhytosanitaryPlan]:
    statement = (
        select(PhytosanitaryPlan)
        .where(PhytosanitaryPlan.bonsai_id == bonsai_id)
        .where(PhytosanitaryPlan.status == "active")
    )
    return session.exec(statement).first()


@with_session
def list_phytosanitary_plans(session: Session, bonsai_id: int) -> List[PhytosanitaryPlan]:
    statement = (
        select(PhytosanitaryPlan)
        .where(PhytosanitaryPlan.bonsai_id == bonsai_id)
        .order_by(PhytosanitaryPlan.created_at)
    )
    return session.exec(statement).all()


@with_session
def get_phytosanitary_plan(session: Session, plan_id: int) -> Optional[PhytosanitaryPlan]:
    return session.get(PhytosanitaryPlan, plan_id)


@with_session
def create_phytosanitary_plan(session: Session, plan: PhytosanitaryPlan) -> PhytosanitaryPlan:
    session.add(plan)
    return plan


@with_session
def update_phytosanitary_plan(session: Session, plan: PhytosanitaryPlan) -> PhytosanitaryPlan:
    db_plan = session.get(PhytosanitaryPlan, plan.id)
    if not db_plan:
        return plan
    db_plan.status = plan.status
    db_plan.abandonment_reason = plan.abandonment_reason
    db_plan.abandoned_at = plan.abandoned_at
    db_plan.wiki_path = plan.wiki_path
    session.add(db_plan)
    return db_plan


@with_session
def delete_phytosanitary_plan(session: Session, plan_id: int) -> bool:
    plan = session.get(PhytosanitaryPlan, plan_id)
    if not plan:
        return False
    session.delete(plan)
    return True
