"""API client for DailyConnect."""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import aiohttp

from .const import API_TIMEOUT, BASE_URL

_LOGGER = logging.getLogger(__name__)


class DailyConnectAPI:
    """API client for DailyConnect."""

    def __init__(
        self, 
        email: str, 
        password: str, 
        session: aiohttp.ClientSession | None = None
    ) -> None:
        """Initialize the API client."""
        self.email = email
        self.password = password
        self._session = session
        self._srf_token: str | None = None
        self._headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
        }

    async def authenticate(self) -> bool:
        """Authenticate with DailyConnect and extract the CSRF token."""
        if not self._session:
            raise ValueError("Session not provided")

        # Prepare login data
        login_data = f"username={quote(self.email)}&password={quote(self.password)}"
        timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)

        try:
            async with self._session.post(
                f"{BASE_URL}/Cmd?cmd=UserAuth",
                data=login_data,
                headers={
                    **self._headers,
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                timeout=timeout,
            ) as response:
                content = await response.text()
                
                # Extract the CSRF token from the response
                # Flatten the content to ensure regex matching works
                content = content.replace('\r\n', ' ')
                match = re.search(r"var\s+__srf_token__\s*=\s*'([^']+)'", content)
                
                if match:
                    self._srf_token = match.group(1)
                    _LOGGER.debug("Extracted token: %s", self._srf_token)
                else:
                    _LOGGER.error("Token not found in authentication response")
                    return False
                
                # Accept either 302 or 200 as success
                if response.status in (200, 302):
                    _LOGGER.debug("Login successful (Status: %s)", response.status)
                    return True
                else:
                    _LOGGER.error("Login failed with status: %s", response.status)
                    return False

        except aiohttp.ClientError as err:
            _LOGGER.error("Authentication failed: %s", err)
            return False

    async def get_user_info(self) -> dict | None:
        """Get user information including kids data."""
        if not self._srf_token:
            raise ValueError("Not authenticated")

        data = f"__srf_token__={self._srf_token}&cmd=UserInfoW"
        timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)

        try:
            async with self._session.post(
                f"{BASE_URL}/CmdW?cmd=UserInfoW",
                data=data,
                headers={
                    **self._headers,
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
                },
                timeout=timeout,
            ) as response:
                if response.status == 200:
                    content = await response.text()
                    _LOGGER.debug("User info response: %s", content[:500])  # Log first 500 chars
                    return await response.json(content_type=None)
                else:
                    _LOGGER.error("Error retrieving user info. Status: %s", response.status)
                    return None

        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to get user info: %s", err)
            return None

    async def get_kid_summary(self, kid_id: str, date: datetime | None = None) -> dict | None:
        """Get kid summary for a specific date (defaults to today)."""
        if not self._srf_token:
            raise ValueError("Not authenticated")

        if date is None:
            date = datetime.now(timezone.utc)

        # Format date as 'yymmdd'
        pdt = date.strftime("%y%m%d")
        data = f"__srf_token__={self._srf_token}&cmd=KidGetSummary&Kid={kid_id}&pdt={pdt}"
        timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)
        _LOGGER.debug("Kid summary request data: %s", data)

        try:
            async with self._session.post(
                f"{BASE_URL}/CmdW",
                data=data,
                headers={
                    **self._headers,
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                timeout=timeout,
            ) as response:
                if response.status == 200:
                    content = await response.text()
                    _LOGGER.debug("Kid summary response for %s: %s", kid_id, content[:500])
                    result = await response.json(content_type=None)
                    _LOGGER.debug("Kid summary parsed for %s: %s", kid_id, result)
                    return result
                else:
                    _LOGGER.error("Error retrieving kid summary. Status: %s", response.status)
                    return None

        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to get kid summary: %s", err)
            return None

    async def get_kid_status(self, kid_id: str, date: datetime | None = None) -> dict | None:
        """Get kid status for a specific date (defaults to today)."""
        if not self._srf_token:
            raise ValueError("Not authenticated")

        if date is None:
            date = datetime.now(timezone.utc)

        # Format date as 'yymmdd'
        pdt = date.strftime("%y%m%d")
        data = f"__srf_token__={self._srf_token}&cmd=StatusList&Kid={kid_id}&pdt={pdt}&fmt=long"
        timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)
        _LOGGER.debug("Kid status request data: %s", data)

        try:
            async with self._session.post(
                f"{BASE_URL}/CmdListW",
                data=data,
                headers={
                    **self._headers,
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
                },
                timeout=timeout,
            ) as response:
                if response.status == 200:
                    content = await response.text()
                    _LOGGER.debug("Kid status response for %s: %s", kid_id, content[:500])
                    result = await response.json(content_type=None)
                    _LOGGER.debug("Kid status parsed for %s: %s", kid_id, result)
                    return result
                else:
                    _LOGGER.error("Error retrieving kid status. Status: %s", response.status)
                    return None

        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to get kid status: %s", err)
            return None

    async def get_calendar_events(
        self, user_id: str, days_ahead: int = 30
    ) -> list | None:
        """Get calendar events for the next N days."""
        if not self._srf_token:
            raise ValueError("Not authenticated")

        now = datetime.now(timezone.utc)
        start_date = now.strftime("%y%m%d")
        end_date = (now + timedelta(days=days_ahead)).strftime("%y%m%d")

        data = (
            f"command=getEvents&start={start_date}&end={end_date}"
            f"&parent=true&uid={user_id}&__srf_token__={self._srf_token}"
        )
        timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)
        _LOGGER.debug("Calendar request data: %s", data)

        try:
            async with self._session.post(
                f"{BASE_URL}/CmdW?cmd=CalendarCmd",
                data=data,
                headers={
                    **self._headers,
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
                },
                timeout=timeout,
            ) as response:
                if response.status == 200:
                    result = await response.json(content_type=None)
                    _LOGGER.debug("Calendar events: %s", result)
                    return result if isinstance(result, list) else []
                else:
                    _LOGGER.error("Error retrieving calendar. Status: %s", response.status)
                    return None

        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to get calendar events: %s", err)
            return None