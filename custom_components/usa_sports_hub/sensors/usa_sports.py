"""Compact per-sport entities for USA Sports Hub."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from ..const import DOMAIN

SECTIONS=("live","fixtures","results","standings","teams","players","news","status")
LABELS={"nfl":"NFL","nba":"NBA","mlb":"MLB","nhl":"NHL"}

async def async_setup_entry(hass,entry,async_add_entities):
    coordinator=hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([UsaSportSensor(coordinator,entry,sport,section) for sport in LABELS for section in SECTIONS])

class UsaSportSensor(SensorEntity):
    _attr_has_entity_name=True
    def __init__(self,coordinator,entry,sport,section):
        self.coordinator=coordinator; self.entry=entry; self.sport=sport; self.section=section
        self._attr_unique_id=f"{entry.entry_id}_{sport}_{section}"; self._attr_name=f"{LABELS[sport]} {section.title()}"
    @property
    def device_info(self): return DeviceInfo(identifiers={(DOMAIN,self.entry.entry_id)},name="USA Sports Hub",manufacturer="USA Sports Hub")
    @property
    def available(self): return self.coordinator.last_update_success
    @property
    def native_value(self):
        data=((self.coordinator.data or {}).get("sports") or {}).get(self.sport,{})
        if self.section=="status": return "Online" if not data.get("error") else "Error"
        if self.section=="players": return 0
        return len(data.get(self.section,[]) or [])
    @property
    def extra_state_attributes(self):
        data=((self.coordinator.data or {}).get("sports") or {}).get(self.sport,{})
        if self.section=="status": return {"provider_error":data.get("error"),"live_polling":(self.coordinator.data or {}).get("live_polling",False)}
        if self.section=="players": return {"players":[],"note":"Player data is added when a team is selected."}
        value=data.get(self.section,[]) or []
        updated=getattr(self.coordinator,"last_update_success_time",None)
        return {self.section:value[:20],"sport":self.sport,"league":LABELS[self.sport],"updated":updated.isoformat() if updated else None}
