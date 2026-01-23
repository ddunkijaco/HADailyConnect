"""Diagnostics support for DailyConnect."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from . import DailyConnectDataUpdateCoordinator
from .const import DOMAIN

TO_REDACT = {CONF_EMAIL, CONF_PASSWORD, "Id", "id", "email", "Email"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: DailyConnectDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    diagnostics_data = {
        "config_entry": {
            "data": async_redact_data(entry.data, TO_REDACT),
            "options": entry.options,
            "version": entry.version,
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "last_update_time": coordinator.last_update_success_time.isoformat()
            if coordinator.last_update_success_time
            else None,
            "update_interval": coordinator.update_interval.total_seconds()
            if coordinator.update_interval
            else None,
        },
        "data": async_redact_data(coordinator.data, TO_REDACT) if coordinator.data else None,
    }

    return diagnostics_data
