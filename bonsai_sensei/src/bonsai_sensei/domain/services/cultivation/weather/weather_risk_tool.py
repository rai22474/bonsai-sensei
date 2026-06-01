from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.resolve_user_id import resolve_confirmation_user_id

WEATHER_RISK_TOOL_DESCRIPTION = (
    "- get_weather_risk: Consulta el pronóstico del tiempo y evalúa riesgos climáticos "
    "(heladas, calor extremo) para bonsáis. "
    "Parámetros: location (str, opcional — ciudad o coordenadas; si se omite usa la ubicación registrada del usuario)."
)


def create_weather_risk_tool(get_user_settings_func: Callable, get_weather_func: Callable) -> Callable:
    async def get_weather_risk(
        location: str = "",
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Get weather forecast and evaluate climate risk for bonsais.

        If location is not provided, uses the user's registered location from session.

        Args:
            location: City name or coordinates. Leave empty to use the user's saved location.

        Returns:
            Weather dict with status 'success' and weather data, or {"status": "no_location"}.
        """
        effective_location = location
        if not effective_location:
            user_id = resolve_confirmation_user_id(tool_context)
            user_settings = get_user_settings_func(user_id) if user_id else None
            effective_location = user_settings.location if user_settings else None

        if not effective_location:
            return {"status": "no_location", "message": "No location registered. Ask the user for their location."}

        return await get_weather_func(effective_location)

    return get_weather_risk
