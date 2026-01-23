"""The DailyConnect integration."""
from __future__ import annotations

import asyncio
import logging
import socket
from datetime import timedelta

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DailyConnectAPI
from .const import CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.CALENDAR,
    Platform.IMAGE,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up DailyConnect from a config entry."""
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]

    # Get update interval from options, or use default
    update_interval = entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

    # Create IPv4-only session to avoid issues with static IPv6 configurations
    connector = aiohttp.TCPConnector(family=socket.AF_INET)
    session = aiohttp.ClientSession(connector=connector)

    api = DailyConnectAPI(email, password, session)

    coordinator = DailyConnectDataUpdateCoordinator(
        hass, api, session, update_interval, entry
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register listener for options updates
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        # Close the custom session
        await coordinator.session.close()

    return unload_ok


class DailyConnectDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the DailyConnect API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: DailyConnectAPI,
        session: aiohttp.ClientSession,
        update_interval: int,
        entry: ConfigEntry,
    ) -> None:
        """Initialize."""
        self.api = api
        self.session = session
        self.entry = entry
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=update_interval),
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            auth_success = await self.api.authenticate()
            if not auth_success:
                raise ConfigEntryAuthFailed("Authentication failed")

            user_info = await self.api.get_user_info()

            _LOGGER.debug("User info received: %s", user_info)

            if not user_info or "myKids" not in user_info:
                raise UpdateFailed("No kids data found")

            kids_data = {}

            # Fetch all kids data in parallel
            async def fetch_kid_data(kid):
                kid_id = kid["Id"]
                kid_name = kid["Name"]

                # Fetch summary and status in parallel
                summary, status = await asyncio.gather(
                    self.api.get_kid_summary(kid_id),
                    self.api.get_kid_status(kid_id),
                )

                _LOGGER.debug(
                    "Kid %s (%s) - Summary: %s, Status: %s",
                    kid_name,
                    kid_id,
                    summary,
                    status,
                )

                return kid_id, {
                    "name": kid_name,
                    "summary": summary,
                    "status": status,
                }

            results = await asyncio.gather(
                *[fetch_kid_data(kid) for kid in user_info["myKids"]]
            )

            for kid_id, data in results:
                kids_data[kid_id] = data

            # Fetch calendar events (use user ID from user_info)
            user_id = user_info.get("Id", "")
            calendar_events = []
            if user_id:
                calendar_events = await self.api.get_calendar_events(user_id) or []

            return {
                "kids": kids_data,
                "calendar": calendar_events,
                "user_id": user_id,
            }

        except ConfigEntryAuthFailed:
            raise
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except (KeyError, TypeError) as err:
            raise UpdateFailed(f"Error parsing API response: {err}") from err