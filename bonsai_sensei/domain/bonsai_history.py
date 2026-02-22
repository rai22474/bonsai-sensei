from typing import List
from sqlmodel import select, Session
from bonsai_sensei.domain.bonsai_event import BonsaiEvent
from bonsai_sensei.database.session_wrapper import with_session


@with_session
def record_bonsai_event(session: Session, bonsai_event: BonsaiEvent) -> BonsaiEvent:
    session.add(bonsai_event)
    return bonsai_event


@with_session
def list_bonsai_events(session: Session, bonsai_id: int) -> List[dict]:
    statement = select(BonsaiEvent).where(BonsaiEvent.bonsai_id == bonsai_id).order_by(BonsaiEvent.occurred_at)
    events = session.exec(statement).all()
    return [
        {
            "id": event.id,
            "bonsai_id": event.bonsai_id,
            "event_type": event.event_type,
            "payload": event.payload,
            "occurred_at": event.occurred_at.isoformat(),
        }
        for event in events
    ]
