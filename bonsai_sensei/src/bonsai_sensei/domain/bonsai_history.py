from datetime import datetime, timedelta, timezone
from typing import List
from sqlmodel import select, Session
from bonsai_sensei.domain.bonsai_event import BonsaiEvent
from bonsai_sensei.database.session_wrapper import with_session


@with_session
def record_bonsai_event(session: Session, bonsai_event: BonsaiEvent) -> BonsaiEvent:
    session.add(bonsai_event)
    return bonsai_event


@with_session
def get_recent_unlinked_pest_events(session: Session, bonsai_id: int, hours: int = 168) -> List[BonsaiEvent]:
    """Return pest_detection events with no linked phytosanitary_application within the last `hours`."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    pest_events = session.exec(
        select(BonsaiEvent)
        .where(BonsaiEvent.bonsai_id == bonsai_id)
        .where(BonsaiEvent.event_type == "pest_detection")
        .where(BonsaiEvent.occurred_at >= cutoff)
        .order_by(BonsaiEvent.occurred_at.desc())
    ).all()

    phyto_events = session.exec(
        select(BonsaiEvent)
        .where(BonsaiEvent.bonsai_id == bonsai_id)
        .where(BonsaiEvent.event_type == "phytosanitary_application")
    ).all()

    linked_ids = {
        event.payload.get("pest_event_id")
        for event in phyto_events
        if event.payload.get("pest_event_id") is not None
    }

    return [event for event in pest_events if event.id not in linked_ids]


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
