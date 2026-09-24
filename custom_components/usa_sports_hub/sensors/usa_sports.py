"""Detailed per-sport entities for USA Sports Hub."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo

from ..const import DOMAIN


SECTIONS = (
    "live",
    "fixtures",
    "results",
    "standings",
    "teams",
    "players",
    "news",
    "game_detail",
    "box_score",
    "play_by_play",
    "drives",
    "scoring",
    "lineups",
    "injuries",
    "statistics",
    "leaders",
    "periods",
    "officials",
    "situations",
    "related",
    "odds",
    "stadium",
    "ticker",
    "status",
)
LABELS = {"nfl": "NFL", "nba": "NBA", "mlb": "MLB", "nhl": "NHL"}
DETAIL_KEYS = {
    "live", "fixtures", "results", "standings", "teams", "players", "news",
    "game_detail", "box_score", "play_by_play", "drives", "scoring",
    "lineups", "injuries", "statistics", "leaders", "periods", "officials",
    "situations", "related", "odds", "stadium", "ticker",
}


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(
        [
            UsaSportSensor(coordinator, entry, sport, section)
            for sport in LABELS
            for section in SECTIONS
        ]
    )


class UsaSportSensor(SensorEntity):
    _attr_has_entity_name = True
    _unrecorded_attributes = frozenset(DETAIL_KEYS)

    def __init__(self, coordinator, entry, sport, section):
        self.coordinator = coordinator
        self.entry = entry
        self.sport = sport
        self.section = section
        self._attr_unique_id = f"{entry.entry_id}_{sport}_{section}"
        self._attr_name = f"{LABELS[sport]} {section.replace('_', ' ').title()}"

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name="USA Sports Hub",
            manufacturer="USA Sports Hub",
            model="TS live sports data",
        )

    @property
    def available(self):
        return self.coordinator.last_update_success

    @property
    def native_value(self):
        data = ((self.coordinator.data or {}).get("sports") or {}).get(self.sport, {})
        if self.section == "status":
            return "Online" if not data.get("error") else "Error"
        value = data.get(self.section)
        if isinstance(value, list):
            return len(value)
        if isinstance(value, dict):
            if self.section == "game_detail":
                return value.get("status_detail") or value.get("status") or (
                    "Available" if value else "Unavailable"
                )
            return len(value)
        return value if value is not None else 0

    @property
    def extra_state_attributes(self):
        data = ((self.coordinator.data or {}).get("sports") or {}).get(self.sport, {})
        updated = getattr(self.coordinator, "last_update_success_time", None)

        if self.section == "status":
            return {
                "provider": "TS",
                "provider_error": data.get("error"),
                "live_polling": (self.coordinator.data or {}).get("live_polling", False),
                "selected_game": (data.get("game_detail") or {}).get("game_id"),
                "api_base": "TS",
            }

        value = data.get(self.section)
        if value is None:
            value = [] if self.section not in {"game_detail", "box_score", "odds", "stadium"} else {}

        # Detailed attributes are intentionally unrecorded so Home Assistant's
        # recorder is not flooded by rapid live play-by-play updates.
        return {
            self.section: value,
            "sport": self.sport,
            "league": LABELS[self.sport],
            "provider": "TS",
            "updated": updated.isoformat() if updated else None,
        }
