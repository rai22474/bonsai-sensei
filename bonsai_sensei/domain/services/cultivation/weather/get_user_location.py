from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.resolve_user_id import resolve_confirmation_user_id


def create_get_user_location_tool(get_user_settings_func: Callable) -> Callable:
    def get_user_location(tool_context: ToolContext | None = None) -> dict:
        """Return the saved location for the current user.

        Uses the user_id from the session context to look up the registered location.
        Call this tool first whenever the user's location is needed but not provided in the message.

        Returns:
            {"location": "<location>"} if the location is registered.
            {"location": null} if the user has no location registered.
        """
        user_id = resolve_confirmation_user_id(tool_context)
        if not user_id:
            return {"location": None}
        user_settings = get_user_settings_func(user_id)
        if not user_settings or not user_settings.location:
            return {"location": None}
        return {"location": user_settings.location}

    return get_user_location
