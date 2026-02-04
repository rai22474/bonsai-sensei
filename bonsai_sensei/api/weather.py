import os
from typing import Callable

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from bonsai_sensei.domain.services.cultivation.weather.weather_tool import create_weather_tool

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
