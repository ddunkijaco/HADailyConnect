"""Image platform for DailyConnect integration."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DailyConnectDataUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up DailyConnect image entities from a config entry."""
    coordinator: DailyConnectDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[ImageEntity] = []

    if coordinator.data and "kids" in coordinator.data:
        for kid_id, kid_data in coordinator.data["kids"].items():
            kid_name = kid_data["name"]

            # Create latest photo image entity for each kid
            entities.append(
                DailyConnectLatestPhotoImage(
                    coordinator,
                    kid_id,
                    kid_name,
                )
            )

    async_add_entities(entities)


class DailyConnectLatestPhotoImage(CoordinatorEntity, ImageEntity):
    """Represents the latest photo from DailyConnect activities."""

    _attr_content_type = "image/jpeg"

    def __init__(
        self,
        coordinator: DailyConnectDataUpdateCoordinator,
        kid_id: str,
        kid_name: str,
    ) -> None:
        """Initialize the image entity."""
        super().__init__(coordinator)
        ImageEntity.__init__(self, coordinator.hass)
        self._kid_id = str(kid_id)  # Ensure string type for consistent key matching
        self._kid_name = kid_name
        self._attr_name = f"{kid_name} Latest Photo"
        self._attr_unique_id = f"{DOMAIN}_{kid_id}_latest_photo"
        self._attr_icon = "mdi:image"
        self._cached_image: bytes | None = None
        self._current_photo_id: str | None = None

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
        last_update = self.coordinator.last_update_success
        has_data = self.coordinator.data is not None
        has_kids = "kids" in self.coordinator.data if has_data else False
        kid_in_data = self._kid_id in self.coordinator.data["kids"] if has_kids else False

        _LOGGER.debug(
            "Image entity %s available check: last_update=%s, has_data=%s, has_kids=%s, "
            "kid_id=%s, kid_in_data=%s, keys=%s",
            self._kid_name, last_update, has_data, has_kids,
            self._kid_id, kid_in_data,
            list(self.coordinator.data["kids"].keys()) if has_kids else []
        )

        return last_update and has_data and has_kids and kid_in_data

    def _get_kid_data(self) -> dict[str, Any] | None:
        """Get kid data from coordinator."""
        if (
            not self.coordinator.data
            or "kids" not in self.coordinator.data
            or self._kid_id not in self.coordinator.data["kids"]
        ):
            return None
        return self.coordinator.data["kids"][self._kid_id]

    def _get_latest_photo_id(self) -> str | None:
        """Get the latest photo ID from activities."""
        kid_data = self._get_kid_data()
        if not kid_data:
            return None

        status_data = kid_data.get("status", {})
        if not isinstance(status_data, dict):
            return None

        activities = status_data.get("list", [])
        if not isinstance(activities, list):
            return None

        # Iterate through activities in reverse to find the latest photo
        # Photos can be attached to various activity types (Cat 1000, 700, etc.)
        # Skip sign in (101) and sign out (102) photos
        for activity in reversed(activities):
            if not isinstance(activity, dict):
                continue

            # Skip sign in/out activities
            cat = activity.get("Cat")
            if cat in (101, 102):
                continue

            # Check if activity has a Photo field
            photo_id = activity.get("Photo")
            if photo_id:
                return str(photo_id)

        return None

    async def async_image(self) -> bytes | None:
        """Return bytes of image."""
        photo_id = self._get_latest_photo_id()

        # If no photo available, return None
        if not photo_id:
            _LOGGER.debug("No photo available for %s", self._kid_name)
            return None

        # If we already have this photo cached, return it
        if photo_id == self._current_photo_id and self._cached_image:
            _LOGGER.debug("Returning cached photo for %s", self._kid_name)
            return self._cached_image

        # Fetch the new photo
        _LOGGER.debug("Fetching photo %s for %s", photo_id, self._kid_name)
        photo_data = await self.coordinator.api.get_photo(photo_id, thumbnail=False)

        if photo_data:
            self._cached_image = photo_data
            self._current_photo_id = photo_id
            _LOGGER.debug("Successfully fetched photo %s for %s, size: %d bytes",
                         photo_id, self._kid_name, len(photo_data))
            return photo_data

        _LOGGER.warning("Failed to fetch photo %s for %s", photo_id, self._kid_name)
        return None

    @property
    def image_last_updated(self) -> datetime | None:
        """Return the timestamp of the last image update."""
        # Return current time if we have a photo, None otherwise
        if self._get_latest_photo_id():
            return datetime.now()
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        photo_id = self._get_latest_photo_id()
        if photo_id:
            return {"photo_id": photo_id}
        return None
