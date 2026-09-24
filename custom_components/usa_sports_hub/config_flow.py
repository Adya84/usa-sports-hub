"""Config flow for USA Sports Hub."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN


class UsaSportsHubConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up USA Sports Hub using TS public data."""

    VERSION = 3

    async def async_step_user(self, user_input=None):
        """Create the single USA Sports Hub entry without credentials."""
        if user_input is not None:
            await self.async_set_unique_id("usa_sports_hub")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title="USA Sports Hub",
                data={"provider_mode": "ts"},
            )

        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))
