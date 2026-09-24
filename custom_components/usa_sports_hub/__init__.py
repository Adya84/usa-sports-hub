"""USA Sports Hub integration setup."""
from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .coordinator import UsaSportsCoordinator
from .const import DOMAIN
from .headshots import MlbHeadshotView

PLATFORMS = ["sensor"]
PANEL_URL = "usa-sports-hub"
PANEL_NAME = "usa-sports-hub-panel"
PANEL_VERSION = "0.0.4-beta.5"
PANEL_STATIC_URL = "/usa_sports_hub/usa-sports-hub-panel.js"
PANEL_MODULE_URL = f"{PANEL_STATIC_URL}?v={PANEL_VERSION}"
PANEL_SCRIPT_PATH = Path(__file__).parent / "frontend" / "usa-sports-hub-panel.js"
PANEL_BACKGROUND_URL = "/usa_sports_hub/usa-sports-hub-background.png"
PANEL_BACKGROUND_PATH = Path(__file__).parent / "frontend" / "usa-sports-hub-background.png"
PANEL_LOGO_URL = "/usa_sports_hub/usa-sports-hub-logo.png"
PANEL_LOGO_PATH = Path(__file__).parent / "frontend" / "usa-sports-hub-logo.png"
PANEL_ICON_URL = "/usa_sports_hub/icon.png"
PANEL_ICON_PATH = Path(__file__).parent / "icon.png"
PANEL_ASSETS_URL = "/usa_sports_hub/assets"
PANEL_ASSETS_PATH = Path(__file__).parent / "frontend"
PANEL_SOUNDS_URL = "/usa_sports_hub/sounds"
PANEL_SOUNDS_PATH = Path(__file__).parent / "frontend" / "sounds"


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = dict(entry.data)
    data["provider_mode"] = "ts"
    hass.config_entries.async_update_entry(entry, data=data, version=3)
    return True



async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    if not hass.data[DOMAIN].get("mlb_headshot_view"):
        hass.http.register_view(MlbHeadshotView(hass))
        hass.data[DOMAIN]["mlb_headshot_view"] = True
    await hass.http.async_register_static_paths([
        StaticPathConfig(PANEL_STATIC_URL, str(PANEL_SCRIPT_PATH), False),
        StaticPathConfig(PANEL_BACKGROUND_URL, str(PANEL_BACKGROUND_PATH), False),
        StaticPathConfig(PANEL_LOGO_URL, str(PANEL_LOGO_PATH), False),
        StaticPathConfig(PANEL_ICON_URL, str(PANEL_ICON_PATH), False),
        StaticPathConfig(PANEL_ASSETS_URL, str(PANEL_ASSETS_PATH), False),
        StaticPathConfig(PANEL_SOUNDS_URL, str(PANEL_SOUNDS_PATH), False),
    ])
    async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title="USA Sports Hub",
        sidebar_icon="mdi:soccer",
        frontend_url_path=PANEL_URL,
        config={"_panel_custom": {"name": PANEL_NAME, "module_url": PANEL_MODULE_URL, "embed_iframe": False, "trust_external": False}},
        require_admin=False,
        update=PANEL_URL in hass.data.get("frontend_panels", {}),
    )

    async def _coordinators(call: ServiceCall):
        entry_id = str(call.data.get("entry_id") or "").strip()
        for runtime_entry_id, runtime in list(hass.data.get(DOMAIN, {}).items()):
            if entry_id and runtime_entry_id != entry_id:
                continue
            if isinstance(runtime, dict) and runtime.get("coordinator") is not None:
                yield runtime["coordinator"]

    async def async_select_live_match(call: ServiceCall) -> None:
        fixture_id = str(call.data.get("fixture_id") or "").strip()
        sport = str(call.data.get("sport") or "").strip().lower()
        async for coordinator in _coordinators(call):
            await coordinator.async_set_selected_live_match(fixture_id, sport=sport)

    async def async_select_team(call: ServiceCall) -> None:
        sport = str(call.data.get("sport") or "").strip().lower()
        team_id = str(call.data.get("team_id") or "").strip()
        async for coordinator in _coordinators(call):
            await coordinator.async_select_team(sport, team_id)

    async def async_add_team_favourite(call: ServiceCall) -> None:
        sport = str(call.data.get("sport") or "").strip().lower()
        team_id = str(call.data.get("team_id") or "").strip()
        team = str(call.data.get("team") or "").strip()
        async for coordinator in _coordinators(call):
            await coordinator.async_add_team_favourite(sport, team_id, team)

    async def async_remove_team_favourite(call: ServiceCall) -> None:
        sport = str(call.data.get("sport") or "").strip().lower()
        team_id = str(call.data.get("team_id") or "").strip()
        async for coordinator in _coordinators(call):
            await coordinator.async_remove_team_favourite(sport, team_id)

    async def async_refresh(call: ServiceCall) -> None:
        async for coordinator in _coordinators(call):
            await coordinator.async_request_refresh()

    # Register only services implemented by the active USA Sports coordinator.
    # Legacy Football Hub services are intentionally not exposed because this
    # coordinator has no matching methods for them.
    services = {
        "select_live_match": async_select_live_match,
        "select_team": async_select_team,
        "add_team_favourite": async_add_team_favourite,
        "remove_team_favourite": async_remove_team_favourite,
        "refresh": async_refresh,
    }
    for name, handler in services.items():
        if not hass.services.has_service(DOMAIN, name):
            hass.services.async_register(DOMAIN, name, handler)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    coordinator = UsaSportsCoordinator(hass, entry)
    restored = await coordinator.async_restore_cache()
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # A restored cache lets the panel and sensors render straight away. Refresh
    # it after setup so Home Assistant never waits on four provider calls just
    # to show the last known scores, fixtures and player data.
    if restored:
        hass.async_create_task(coordinator.async_config_entry_first_refresh())
    else:
        await coordinator.async_config_entry_first_refresh()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok

