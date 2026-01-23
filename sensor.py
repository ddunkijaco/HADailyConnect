"""Sensor platform for DailyConnect integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
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
    """Set up DailyConnect sensors from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    if coordinator.data:
        for kid_id, kid_data in coordinator.data.items():
            kid_name = kid_data["name"]
            
            # Create individual sensors for each data type
            entities.extend([
                # Sleep sensors
                DailyConnectSleepStatusSensor(coordinator, kid_id, kid_name),
                DailyConnectSleepCountSensor(coordinator, kid_id, kid_name),
                DailyConnectSleepDurationSensor(coordinator, kid_id, kid_name),
                DailyConnectLastSleepSensor(coordinator, kid_id, kid_name),
                
                # Feeding sensors
                DailyConnectBottleCountSensor(coordinator, kid_id, kid_name),
                DailyConnectBottleVolumeSensor(coordinator, kid_id, kid_name),
                DailyConnectLastBottleSensor(coordinator, kid_id, kid_name),
                DailyConnectLastFoodSensor(coordinator, kid_id, kid_name),
                
                # Diaper sensors
                DailyConnectDiaperCountSensor(coordinator, kid_id, kid_name),
                DailyConnectWetDiaperCountSensor(coordinator, kid_id, kid_name),
                DailyConnectBMDiaperCountSensor(coordinator, kid_id, kid_name),
                DailyConnectLastDiaperSensor(coordinator, kid_id, kid_name),
                
                # Activity sensor (status)
                DailyConnectActivitySensor(coordinator, kid_id, kid_name),
            ])
    
    async_add_entities(entities)


class DailyConnectBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for DailyConnect sensors."""

    def __init__(
        self,
        coordinator: DailyConnectDataUpdateCoordinator,
        kid_id: str,
        kid_name: str,
        sensor_type: str,
        icon: str = "mdi:account-child",
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._kid_id = kid_id
        self._kid_name = kid_name
        self._sensor_type = sensor_type
        self._attr_name = f"{kid_name} {sensor_type}"
        self._attr_unique_id = f"{DOMAIN}_{kid_id}_{sensor_type.lower().replace(' ', '_')}"
        self._attr_icon = icon

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
            and self._kid_id in self.coordinator.data
        )

    def get_summary_data(self):
        """Get summary data for the kid."""
        if not self.coordinator.data or self._kid_id not in self.coordinator.data:
            return None
        
        summary_data = self.coordinator.data[self._kid_id].get("summary")
        if summary_data and isinstance(summary_data, dict) and "summary" in summary_data:
            return summary_data["summary"]
        return None


# Sleep Sensors
class DailyConnectSleepStatusSensor(DailyConnectBaseSensor):
    """Sleep status sensor."""

    def __init__(self, coordinator, kid_id, kid_name):
        super().__init__(coordinator, kid_id, kid_name, "Sleep Status", "mdi:sleep")

    @property
    def state(self) -> str | None:
        summary = self.get_summary_data()
        if summary:
            return "sleeping" if summary.get("isSleeping", False) else "awake"
        return "unknown"


class DailyConnectSleepCountSensor(DailyConnectBaseSensor):
    """Sleep count sensor."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, coordinator, kid_id, kid_name):
        super().__init__(coordinator, kid_id, kid_name, "Sleep Count", "mdi:counter")

    @property
    def state(self) -> int | None:
        summary = self.get_summary_data()
        return summary.get("nrOfSleep", 0) if summary else None

    @property
    def native_unit_of_measurement(self) -> str:
        return "naps"


class DailyConnectSleepDurationSensor(DailyConnectBaseSensor):
    """Sleep duration sensor."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "min"

    def __init__(self, coordinator, kid_id, kid_name):
        super().__init__(coordinator, kid_id, kid_name, "Sleep Duration", "mdi:clock")

    @property
    def state(self) -> int | None:
        summary = self.get_summary_data()
        return summary.get("totalSleepDuration", 0) if summary else None


class DailyConnectLastSleepSensor(DailyConnectBaseSensor):
    """Last sleep time sensor."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, kid_id, kid_name):
        super().__init__(coordinator, kid_id, kid_name, "Last Sleep", "mdi:clock-outline")

    @property
    def state(self) -> str | None:
        summary = self.get_summary_data()
        return summary.get("timeOfLastSleeping") if summary else None


# Feeding Sensors
class DailyConnectBottleCountSensor(DailyConnectBaseSensor):
    """Bottle count sensor."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, coordinator, kid_id, kid_name):
        super().__init__(coordinator, kid_id, kid_name, "Bottle Count", "mdi:baby-bottle")

    @property
    def state(self) -> int | None:
        summary = self.get_summary_data()
        return summary.get("nrOfBottle", 0) if summary else None

    @property
    def native_unit_of_measurement(self) -> str:
        return "bottles"


class DailyConnectBottleVolumeSensor(DailyConnectBaseSensor):
    """Bottle volume sensor."""

    _attr_device_class = SensorDeviceClass.VOLUME
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "oz"

    def __init__(self, coordinator, kid_id, kid_name):
        super().__init__(coordinator, kid_id, kid_name, "Bottle Volume", "mdi:baby-bottle-outline")

    @property
    def state(self) -> float | None:
        summary = self.get_summary_data()
        return summary.get("totalBottleSize", 0) if summary else None


class DailyConnectLastBottleSensor(DailyConnectBaseSensor):
    """Last bottle time sensor."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, kid_id, kid_name):
        super().__init__(coordinator, kid_id, kid_name, "Last Bottle", "mdi:clock-outline")

    @property
    def state(self) -> str | None:
        summary = self.get_summary_data()
        return summary.get("timeOfLastBottle") if summary else None


class DailyConnectLastFoodSensor(DailyConnectBaseSensor):
    """Last food time sensor."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, kid_id, kid_name):
        super().__init__(coordinator, kid_id, kid_name, "Last Food", "mdi:food")

    @property
    def state(self) -> str | None:
        summary = self.get_summary_data()
        return summary.get("timeOfLastFood") if summary else None


# Diaper Sensors
class DailyConnectDiaperCountSensor(DailyConnectBaseSensor):
    """Total diaper count sensor."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, coordinator, kid_id, kid_name):
        super().__init__(coordinator, kid_id, kid_name, "Diaper Count", "mdi:baby")

    @property
    def state(self) -> int | None:
        summary = self.get_summary_data()
        return summary.get("nrOfDiapers", 0) if summary else None

    @property
    def native_unit_of_measurement(self) -> str:
        return "diapers"


class DailyConnectWetDiaperCountSensor(DailyConnectBaseSensor):
    """Wet diaper count sensor."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, coordinator, kid_id, kid_name):
        super().__init__(coordinator, kid_id, kid_name, "Wet Diapers", "mdi:water")

    @property
    def state(self) -> int | None:
        summary = self.get_summary_data()
        return summary.get("nrOfWetDiapers", 0) if summary else None

    @property
    def native_unit_of_measurement(self) -> str:
        return "diapers"


class DailyConnectBMDiaperCountSensor(DailyConnectBaseSensor):
    """BM diaper count sensor."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, coordinator, kid_id, kid_name):
        super().__init__(coordinator, kid_id, kid_name, "BM Diapers", "mdi:baby")

    @property
    def state(self) -> int | None:
        summary = self.get_summary_data()
        return summary.get("nrOfBMDiapers", 0) if summary else None

    @property
    def native_unit_of_measurement(self) -> str:
        return "diapers"


class DailyConnectLastDiaperSensor(DailyConnectBaseSensor):
    """Last diaper time sensor."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, kid_id, kid_name):
        super().__init__(coordinator, kid_id, kid_name, "Last Diaper", "mdi:clock-outline")

    @property
    def state(self) -> str | None:
        summary = self.get_summary_data()
        return summary.get("timeOfLastDiaper") if summary else None


# Activity Sensor
class DailyConnectActivitySensor(DailyConnectBaseSensor):
    """Activity count sensor."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, coordinator, kid_id, kid_name):
        super().__init__(coordinator, kid_id, kid_name, "Activities", "mdi:calendar-today")

    @property
    def state(self) -> int | None:
        if not self.coordinator.data or self._kid_id not in self.coordinator.data:
            return None

        status_data = self.coordinator.data[self._kid_id].get("status")
        if status_data and isinstance(status_data, dict):
            activities = status_data.get("list", [])
            return len(activities)
        return 0

    @property
    def native_unit_of_measurement(self) -> str:
        return "activities"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if not self.coordinator.data or self._kid_id not in self.coordinator.data:
            return None
        
        status_data = self.coordinator.data[self._kid_id].get("status")
        if status_data and isinstance(status_data, dict):
            activities = status_data.get("list", [])
            
            # Get recent activities (last 5)
            recent_activities = []
            for activity in activities[-5:]:
                activity_info = {
                    "time": activity.get("Utm", ""),
                    "description": activity.get("Txt", ""),
                    "category": activity.get("Cat", ""),
                }
                recent_activities.append(activity_info)
            
            return {"recent_activities": recent_activities} if recent_activities else None
        
        return None