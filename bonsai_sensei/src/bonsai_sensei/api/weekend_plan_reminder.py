from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from bonsai_sensei.domain.services.cultivation.plan.weekend_plan_runner import run_weekend_plan_reminders

router = APIRouter()


@router.post("/cultivation/plan/weekend-reminder/trigger")
async def trigger_weekend_plan_reminder(request: Request):
    async def event_stream():
        async for reminder_json in run_weekend_plan_reminders(
            advisor=request.app.state.advisor,
            list_all_user_settings_func=request.app.state.user_settings_service["list_all_user_settings"],
            list_planned_works_in_date_range_func=request.app.state.cultivation_plan_service["list_planned_works_in_date_range"],
            list_bonsai_func=request.app.state.garden_service["list_bonsai"],
            send_telegram_message_func=request.app.state.bot.send_message,
        ):
            yield f"data: {reminder_json}\n\n"
        yield 'data: {"status": "done"}\n\n'

    return StreamingResponse(event_stream(), media_type="text/event-stream")
