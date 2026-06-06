from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from bonsai_sensei.domain.services.cultivation.mimamori.runner import run_mimamori
from bonsai_sensei.domain.services.cultivation.weather.weather import fetch_weather

router = APIRouter()


@router.post("/mimamori/trigger")
async def trigger_mimamori(request: Request):
    async def event_stream():
        async for reflection_json in run_mimamori(
            advisor=request.app.state.advisor,
            list_all_user_settings_func=request.app.state.user_settings_service["list_all_user_settings"],
            list_bonsai_func=request.app.state.garden_service["list_bonsai"],
            list_species_func=request.app.state.herbarium_service["list_species"],
            list_bonsai_events_func=request.app.state.bonsai_history_service["list_bonsai_events"],
            get_active_development_plan_func=request.app.state.development_plan_service["get_active_development_plan"],
            list_planned_works_in_date_range_func=request.app.state.cultivation_plan_service["list_planned_works_in_date_range"],
            fetch_weather_func=fetch_weather,
            send_telegram_message_func=request.app.state.bot.send_message,
        ):
            yield f"data: {reflection_json}\n\n"
        yield 'data: {"status": "done"}\n\n'

    return StreamingResponse(event_stream(), media_type="text/event-stream")
