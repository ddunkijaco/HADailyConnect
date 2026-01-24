"""Sensor platform for DailyConnect integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DailyConnectDataUpdateCoordinator
from .const import DOMAIN


@dataclass(frozen=True)
class DailyConnectSensorEntityDescription(SensorEntityDescription):
    """Describes DailyConnect sensor entity."""

    value_fn: Callable[[dict[str, Any]], StateType] | None = None
    attributes_fn: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None
    icon_fn: Callable[[dict[str, Any]], str] | None = None


# Activity category codes
CAT_POTTY = 2300
CAT_MEDICATION = 1500
CAT_NEED = 3000


def _count_activities_by_cat(data: dict[str, Any], cat: int) -> int:
    """Count activities by category code."""
    activities = data.get("status", {}).get("list", [])
    return sum(1 for a in activities if a.get("Cat") == cat)


def _get_activities_by_cat(data: dict[str, Any], cat: int) -> list[dict[str, Any]]:
    """Get all activities of a specific category."""
    activities = data.get("status", {}).get("list", [])
    return [a for a in activities if a.get("Cat") == cat]


def _get_last_activity_time_by_cat(data: dict[str, Any], cat: int) -> str | None:
    """Get the timestamp of the last activity of a category."""
    activities = _get_activities_by_cat(data, cat)
    if activities:
        return activities[-1].get("Utm")
    return None


# Sleep sensors
SLEEP_SENSORS = [
    DailyConnectSensorEntityDescription(
        key="sleep_status",
        translation_key="sleep_status",
        name="Sleep Status",
        icon="mdi:sleep",
        value_fn=lambda data: (
            "sleeping"
            if data.get("summary", {}).get("summary", {}).get("isSleeping", False)
            else "awake"
        ),
    ),
    DailyConnectSensorEntityDescription(
        key="sleep_count",
        translation_key="sleep_count",
        name="Sleep Count",
        icon="mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="naps",
        value_fn=lambda data: data.get("summary", {}).get("summary", {}).get("nrOfSleep", 0),
    ),
    DailyConnectSensorEntityDescription(
        key="sleep_duration",
        translation_key="sleep_duration",
        name="Sleep Duration",
        icon="mdi:clock",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="min",
        value_fn=lambda data: data.get("summary", {}).get("summary", {}).get("totalSleepDuration", 0),
    ),
    DailyConnectSensorEntityDescription(
        key="last_sleep",
        translation_key="last_sleep",
        name="Last Sleep",
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data.get("summary", {}).get("summary", {}).get("timeOfLastSleeping"),
    ),
]

# Feeding sensors
FEEDING_SENSORS = [
    DailyConnectSensorEntityDescription(
        key="bottle_count",
        translation_key="bottle_count",
        name="Bottle Count",
        icon="mdi:baby-bottle",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="bottles",
        value_fn=lambda data: data.get("summary", {}).get("summary", {}).get("nrOfBottle", 0),
    ),
    DailyConnectSensorEntityDescription(
        key="bottle_volume",
        translation_key="bottle_volume",
        name="Bottle Volume",
        icon="mdi:baby-bottle-outline",
        device_class=SensorDeviceClass.VOLUME,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="fl. oz.",
        value_fn=lambda data: data.get("summary", {}).get("summary", {}).get("totalBottleSize", 0),
    ),
    DailyConnectSensorEntityDescription(
        key="last_bottle",
        translation_key="last_bottle",
        name="Last Bottle",
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data.get("summary", {}).get("summary", {}).get("timeOfLastBottle"),
    ),
    DailyConnectSensorEntityDescription(
        key="last_food",
        translation_key="last_food",
        name="Last Food",
        icon="mdi:food",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data.get("summary", {}).get("summary", {}).get("timeOfLastFood"),
    ),
]

# Diaper sensors
DIAPER_SENSORS = [
    DailyConnectSensorEntityDescription(
        key="diaper_count",
        translation_key="diaper_count",
        name="Diaper Count",
        icon="mdi:baby",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="diapers",
        value_fn=lambda data: data.get("summary", {}).get("summary", {}).get("nrOfDiapers", 0),
    ),
    DailyConnectSensorEntityDescription(
        key="wet_diapers",
        translation_key="wet_diapers",
        name="Wet Diapers",
        icon="mdi:water",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="diapers",
        value_fn=lambda data: data.get("summary", {}).get("summary", {}).get("nrOfWetDiapers", 0),
    ),
    DailyConnectSensorEntityDescription(
        key="bm_diapers",
        translation_key="bm_diapers",
        name="BM Diapers",
        icon="mdi:baby",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="diapers",
        value_fn=lambda data: data.get("summary", {}).get("summary", {}).get("nrOfBMDiapers", 0),
    ),
    DailyConnectSensorEntityDescription(
        key="last_diaper",
        translation_key="last_diaper",
        name="Last Diaper",
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data.get("summary", {}).get("summary", {}).get("timeOfLastDiaper"),
    ),
]

# Activity sensor
ACTIVITY_SENSOR = DailyConnectSensorEntityDescription(
    key="activities",
    translation_key="activities",
    name="Activities",
    icon="mdi:calendar-today",
    state_class=SensorStateClass.TOTAL_INCREASING,
    native_unit_of_measurement="activities",
    value_fn=lambda data: len(data.get("status", {}).get("list", [])),
    attributes_fn=lambda data: {
        "recent_activities": [
            {
                "time": activity.get("Utm", ""),
                "description": activity.get("Txt", ""),
                "category": activity.get("Cat", ""),
                "photo_id": activity.get("Photo") if activity.get("Cat") == 1000 else None,
            }
            for activity in data.get("status", {}).get("list", [])[-5:]
        ]
    }
    if data.get("status", {}).get("list")
    else None,
)

# Potty sensors (for potty training)
POTTY_SENSORS = [
    DailyConnectSensorEntityDescription(
        key="potty_count",
        translation_key="potty_count",
        name="Potty Count",
        icon="mdi:toilet",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="times",
        value_fn=lambda data: _count_activities_by_cat(data, CAT_POTTY),
    ),
    DailyConnectSensorEntityDescription(
        key="last_potty",
        translation_key="last_potty",
        name="Last Potty",
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: _get_last_activity_time_by_cat(data, CAT_POTTY),
    ),
]

# Medication sensors
MEDICATION_SENSORS = [
    DailyConnectSensorEntityDescription(
        key="medication_count",
        translation_key="medication_count",
        name="Medication Count",
        icon="mdi:pill",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="doses",
        value_fn=lambda data: _count_activities_by_cat(data, CAT_MEDICATION),
        attributes_fn=lambda data: {
            "medications_today": [
                {
                    "time": med.get("Utm", ""),
                    "description": med.get("Txt", ""),
                }
                for med in _get_activities_by_cat(data, CAT_MEDICATION)
            ]
        }
        if _get_activities_by_cat(data, CAT_MEDICATION)
        else None,
    ),
    DailyConnectSensorEntityDescription(
        key="last_medication",
        translation_key="last_medication",
        name="Last Medication",
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: _get_last_activity_time_by_cat(data, CAT_MEDICATION),
    ),
]

# Needs/requests sensor
NEEDS_SENSOR = DailyConnectSensorEntityDescription(
    key="needs_count",
    translation_key="needs_count",
    name="Needs",
    icon="mdi:hand-extended",
    state_class=SensorStateClass.TOTAL_INCREASING,
    native_unit_of_measurement="items",
    value_fn=lambda data: _count_activities_by_cat(data, CAT_NEED),
    attributes_fn=lambda data: {
        "needs_today": [
            {
                "time": need.get("Utm", ""),
                "description": need.get("Txt", ""),
            }
            for need in _get_activities_by_cat(data, CAT_NEED)
        ]
    }
    if _get_activities_by_cat(data, CAT_NEED)
    else None,
)

# All kid sensors
KID_SENSORS = [
    *SLEEP_SENSORS,
    *FEEDING_SENSORS,
    *DIAPER_SENSORS,
    ACTIVITY_SENSOR,
    *POTTY_SENSORS,
    *MEDICATION_SENSORS,
    NEEDS_SENSOR,
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up DailyConnect sensors from a config entry."""
    coordinator: DailyConnectDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[SensorEntity] = []

    if coordinator.data and "kids" in coordinator.data:
        for kid_id, kid_data in coordinator.data["kids"].items():
            kid_name = kid_data["name"]

            # Create sensors for this kid
            for description in KID_SENSORS:
                entities.append(
                    DailyConnectKidSensor(
                        coordinator,
                        description,
                        kid_id,
                        kid_name,
                    )
                )

    async_add_entities(entities)


class DailyConnectKidSensor(CoordinatorEntity, SensorEntity):
    """Represents a DailyConnect kid sensor."""

    entity_description: DailyConnectSensorEntityDescription

    def __init__(
        self,
        coordinator: DailyConnectDataUpdateCoordinator,
        description: DailyConnectSensorEntityDescription,
        kid_id: str,
        kid_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._kid_id = kid_id
        self._kid_name = kid_name
        self._attr_name = f"{kid_name} {description.name}"
        self._attr_unique_id = f"{DOMAIN}_{kid_id}_{description.key}"

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
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        kid_data = self._get_kid_data()
        if not kid_data:
            return None

        if self.entity_description.value_fn:
            return self.entity_description.value_fn(kid_data)

        return None

    @property
    def icon(self) -> str | None:
        """Return the icon of the sensor."""
        kid_data = self._get_kid_data()
        if kid_data and self.entity_description.icon_fn:
            return self.entity_description.icon_fn(kid_data)
        return self.entity_description.icon

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        kid_data = self._get_kid_data()
        if not kid_data:
            return None

        if self.entity_description.attributes_fn:
            return self.entity_description.attributes_fn(kid_data)

        return None
