"""Same-origin MLB headshot endpoint for the USA Sports Hub panel."""
from __future__ import annotations

from time import monotonic

from aiohttp import ClientError, web

from homeassistant.components.http import HomeAssistantView
from homeassistant.helpers.aiohttp_client import async_get_clientsession


class MlbHeadshotView(HomeAssistantView):
    """Proxy official MLB portraits so the panel never depends on third-party CSP."""

    url = "/api/usa_sports_hub/mlb/headshot/{player_id}"
    name = "api:usa_sports_hub:mlb_headshot"
    requires_auth = False

    def __init__(self, hass) -> None:
        self._session = async_get_clientsession(hass)
        self._cache: dict[str, tuple[float, bytes, str]] = {}

    async def get(self, request: web.Request, player_id: str) -> web.Response:
        if not player_id.isdecimal():
            raise web.HTTPBadRequest(text="Invalid MLB player id")

        cached = self._cache.get(player_id)
        if cached and monotonic() - cached[0] < 86_400:
            return web.Response(
                body=cached[1], content_type=cached[2],
                headers={"Cache-Control": "public, max-age=86400"},
            )

        source = (
            "https://img.mlbstatic.com/mlb-photos/image/upload/"
            f"w_213,q_auto:best/v1/people/{player_id}/headshot/67/current.png"
        )
        try:
            async with self._session.get(source, timeout=15) as response:
                if response.status != 200:
                    raise web.HTTPNotFound()
                image = await response.read()
                content_type = response.content_type or "image/png"
        except (ClientError, TimeoutError):
            raise web.HTTPServiceUnavailable() from None

        # Keep a compact in-memory cache as a backstop for provider hiccups.
        if len(self._cache) >= 150:
            self._cache.pop(next(iter(self._cache)))
        self._cache[player_id] = (monotonic(), image, content_type)
        return web.Response(
            body=image, content_type=content_type,
            headers={"Cache-Control": "public, max-age=86400"},
        )
