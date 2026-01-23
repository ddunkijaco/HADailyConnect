"""Calendar platform for DailyConnect integration."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import DailyConnectDataUpdateCoordinator
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up DailyConnect calendar from a config entry."""
    coordinator: DailyConnectDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities([DailyConnectCalendar(coordinator)])


class DailyConnectCalendar(CoordinatorEntity, CalendarEntity):
    """Represents a DailyConnect calendar."""

    _attr_icon = "mdi:calendar-star"

    def __init__(self, coordinator: DailyConnectDataUpdateCoordinator) -> None:
        """Initialize the calendar."""
        super().__init__(coordinator)
        self._attr_name = "DailyConnect Calendar"
        self._attr_unique_id = f"{DOMAIN}_calendar_entity"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, "account")},
            "name": "DailyConnect Account",
            "manufacturer": "DailyConnect",
            "model": "Account",
        }

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming calendar event."""
        if not self.coordinator.data:
            return None

        events = self.coordinator.data.get("calendar", [])
        if not events:
            return None

        # Get the first upcoming event
        now = dt_util.now()
        for event_data in events:
            start_str = event_data.get("start")
            if not start_str:
                continue

            try:
                # Parse the start date/time
                # DailyConnect returns dates in format like "2024-01-23" or "2024-01-23T10:00:00"
                if "T" in start_str:
                    start = dt_util.parse_datetime(start_str)
                else:
                    start = dt_util.parse_date(start_str)
                    if start:
                        start = datetime.combine(start, datetime.min.time())
                        start = dt_util.as_local(start)

                if start and start >= now:
                    end_str = event_data.get("end")
                    end = None
                    if end_str:
                        if "T" in end_str:
                            end = dt_util.parse_datetime(end_str)
                        else:
                            end_date = dt_util.parse_date(end_str)
                            if end_date:
                                end = datetime.combine(end_date, datetime.max.time())
                                end = dt_util.as_local(end)

                    return CalendarEvent(
                        start=start,
                        end=end or start,
                        summary=event_data.get("title", ""),
                        description=event_data.get("description", ""),
                    )
            except (ValueError, TypeError):
                continue

        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        if not self.coordinator.data:
            return []

        events = self.coordinator.data.get("calendar", [])
        if not events:
            return []

        calendar_events = []
        for event_data in events:
            start_str = event_data.get("start")
            if not start_str:
                continue

            try:
                # Parse the start date/time
                if "T" in start_str:
                    event_start = dt_util.parse_datetime(start_str)
                else:
                    event_start_date = dt_util.parse_date(start_str)
                    if event_start_date:
                        event_start = datetime.combine(event_start_date, datetime.min.time())
                        event_start = dt_util.as_local(event_start)
                    else:
                        continue

                if not event_start:
                    continue

                # Parse the end date/time
                end_str = event_data.get("end")
                event_end = None
                if end_str:
                    if "T" in end_str:
                        event_end = dt_util.parse_datetime(end_str)
                    else:
                        event_end_date = dt_util.parse_date(end_str)
                        if event_end_date:
                            event_end = datetime.combine(event_end_date, datetime.max.time())
                            event_end = dt_util.as_local(event_end)

                if not event_end:
                    event_end = event_start

                # Only include events that overlap with the requested range
                if event_start <= end_date and event_end >= start_date:
                    calendar_events.append(
                        CalendarEvent(
                            start=event_start,
                            end=event_end,
                            summary=event_data.get("title", ""),
                            description=event_data.get("description", ""),
                        )
                    )
            except (ValueError, TypeError):
                continue

        return calendar_events
