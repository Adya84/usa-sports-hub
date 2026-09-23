"""Shared HTTP helper."""
from __future__ import annotations
import asyncio
from typing import Any


class ProviderError(RuntimeError): pass

class ProviderClient:
    def __init__(self, session): self.session = session
    async def async_get_json(self, url: str) -> dict[str, Any]:
        try:
            async with self.session.get(url, timeout=20) as response:
                if response.status >= 400: raise ProviderError(f"HTTP {response.status} from {url}")
                return await response.json(content_type=None)
        except (asyncio.TimeoutError, OSError) as err:
            raise ProviderError(f"Unable to reach provider: {err}") from err
