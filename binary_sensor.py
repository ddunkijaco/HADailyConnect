"""Binary sensor platform for DailyConnect integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DailyConnectDataUpdateCoordinator
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up DailyConnect binary sensors from a config entry."""
    coordinator: DailyConnectDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[BinarySensorEntity] = []

    if coordinator.data and "kids" in coordinator.data:
        for kid_id, kid_data in coordinator.data["kids"].items():
            kid_name = kid_data["name"]

            # Create sleep status binary sensor
            entities.append(
                DailyConnectSleepBinarySensor(
                    coordinator,
                    kid_id,
                    kid_name,
                )
            )

    async_add_entities(entities)


class DailyConnectSleepBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Represents a DailyConnect sleep binary sensor."""

    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY
    _attr_icon = "mdi:sleep"

    def __init__(
        self,
        coordinator: DailyConnectDataUpdateCoordinator,
        kid_id: str,
        kid_name: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._kid_id = str(kid_id)  # Ensure string type for consistent key matching
        self._kid_name = kid_name
        self._attr_name = f"{kid_name} Sleeping"
        self._attr_unique_id = f"{DOMAIN}_{kid_id}_sleeping"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._kid_id)},
            "name": self._kid_name,
            "manufacturer": "DailyConnect",
            "model": "Child Profile",
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "kids" in self.coordinator.data
            and self._kid_id in self.coordinator.data["kids"]
        )

    def _get_kid_data(self) -> dict[str, Any] | None:
        """Get kid data from coordinator."""
        if (
            not self.coordinator.data
            or "kids" not in self.coordinator.data
            or self._kid_id not in self.coordinator.data["kids"]
        ):
            return None
        return self.coordinator.data["kids"][self._kid_id]

    @property
    def is_on(self) -> bool:
        """Return true if the child is sleeping."""
        kid_data = self._get_kid_data()
        if not kid_data:
            return False

        summary = kid_data.get("summary", {}).get("summary", {})
        return summary.get("isSleeping", False)

    @property
    def icon(self) -> str:
        """Return the icon based on sleep status."""
        return "mdi:sleep" if self.is_on else "mdi:sleep-off"
