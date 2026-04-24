from typing import Callable
import os

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from bonsai_sensei.domain.services.cultivation.weather.weather import create_weather_tool
from bonsai_sensei.domain.services.cultivation.weather.weather_alert_runner import run_weather_alerts

router = APIRouter()


class WeatherRequest(BaseModel):
    location: str


def get_weather_service() -> Callable[[str], object]:
    base_url = os.getenv("WEATHER_API_BASE", "https://wttr.in")
    return create_weather_tool(base_url)


@router.post("/weather")
async def get_weather_forecast(
    request_body: WeatherRequest,
    weather_service: Callable[[str], object] = Depends(get_weather_service),
):
    return {"forecast": await weather_service(request_body.location)}


@router.post("/weather/alerts/trigger")
async def trigger_weather_alerts(request: Request):
    async def event_stream():
        async for alert_json in run_weather_alerts(
            advisor=request.app.state.advisor,
            list_all_user_settings_func=request.app.state.user_settings_service["list_all_user_settings"],
            send_telegram_message_func=request.app.state.bot.send_message,
        ):
            yield f"data: {alert_json}\n\n"
        yield 'data: {"status": "done"}\n\n'

    return StreamingResponse(event_stream(), media_type="text/event-stream")
