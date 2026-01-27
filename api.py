"""API client for DailyConnect."""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from urllib.parse import quote

import aiohttp

from .const import API_TIMEOUT, BASE_URL

_LOGGER = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAYS = [2, 4, 8]  # Exponential backoff in seconds


async def _retry_with_backoff(
    func: Callable,
    *args: Any,
    max_retries: int = MAX_RETRIES,
    **kwargs: Any
) -> Any:
    """Retry a function with exponential backoff.

    Args:
        func: The async function to retry
        *args: Positional arguments for the function
        max_retries: Maximum number of retry attempts
        **kwargs: Keyword arguments for the function

    Returns:
        The result of the function call

    Raises:
        The last exception if all retries fail
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            last_exception = err
            if attempt < max_retries:
                delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                _LOGGER.warning(
                    "API call failed (attempt %d/%d): %s. Retrying in %ds...",
                    attempt + 1,
                    max_retries + 1,
                    err,
                    delay
                )
                await asyncio.sleep(delay)
            else:
                _LOGGER.error("API call failed after %d attempts: %s", max_retries + 1, err)

    raise last_exception


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
                    _LOGGER.error(
                        "Token not found in authentication response. "
                        "DailyConnect may have changed their login page format. "
                        "Response preview: %s",
                        content[:200]
                    )
                    return False

                # Accept either 302 or 200 as success
                if response.status in (200, 302):
                    _LOGGER.debug("Login successful (Status: %s)", response.status)
                    return True
                else:
                    _LOGGER.error("Login failed with status: %s, response: %s", response.status, content[:200])
                    return False

        except aiohttp.ClientError as err:
            _LOGGER.error("Authentication failed due to network error: %s", err)
            return False
        except Exception as err:
            _LOGGER.exception("Unexpected error during authentication: %s", err)
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
                    result = await response.json(content_type=None)
                    _LOGGER.debug("User info response: %s", str(result)[:500])  # Log first 500 chars

                    # Validate response structure
                    if not isinstance(result, dict):
                        _LOGGER.error("User info response is not a dict: %s", type(result))
                        return None

                    return result
                else:
                    _LOGGER.error("Error retrieving user info. Status: %s", response.status)
                    return None

        except (aiohttp.ClientError, ValueError) as err:
            _LOGGER.error("Failed to get user info: %s", err)
            return None

    async def get_kid_summary(self, kid_id: str, date: datetime | None = None) -> dict | None:
        """Get kid summary for a specific date (defaults to today)."""
        if not self._srf_token:
            raise ValueError("Not authenticated")

        if date is None:
            date = datetime.now()  # Use local time, not UTC

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
                    result = await response.json(content_type=None)
                    _LOGGER.debug("Kid summary response for %s: %s", kid_id, str(result)[:500])

                    # Validate response structure
                    if not isinstance(result, dict):
                        _LOGGER.error("Kid summary response is not a dict for %s: %s", kid_id, type(result))
                        return None

                    return result
                else:
                    _LOGGER.error("Error retrieving kid summary. Status: %s", response.status)
                    return None

        except (aiohttp.ClientError, ValueError) as err:
            _LOGGER.error("Failed to get kid summary: %s", err)
            return None

    async def get_kid_status(self, kid_id: str, date: datetime | None = None) -> dict | None:
        """Get kid status for a specific date (defaults to today)."""
        if not self._srf_token:
            raise ValueError("Not authenticated")

        if date is None:
            date = datetime.now()  # Use local time, not UTC

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
                    result = await response.json(content_type=None)
                    _LOGGER.debug("Kid status response for %s: %s", kid_id, str(result)[:500])

                    # Validate response structure
                    if not isinstance(result, dict):
                        _LOGGER.error("Kid status response is not a dict for %s: %s", kid_id, type(result))
                        return None

                    return result
                else:
                    _LOGGER.error("Error retrieving kid status. Status: %s", response.status)
                    return None

        except (aiohttp.ClientError, ValueError) as err:
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

                    # Validate response structure
                    if not isinstance(result, list):
                        _LOGGER.warning("Calendar events response is not a list: %s, returning empty list", type(result))
                        return []

                    return result
                else:
                    _LOGGER.error("Error retrieving calendar. Status: %s", response.status)
                    return None

        except (aiohttp.ClientError, ValueError) as err:
            _LOGGER.error("Failed to get calendar events: %s", err)
            return None

    async def get_photo(self, photo_id: str, thumbnail: bool = False) -> bytes | None:
        """Get a photo by ID.

        Args:
            photo_id: The photo ID from activity data
            thumbnail: If True, fetch thumbnail (0=full size, 1=thumbnail)

        Returns:
            Binary photo data or None if failed
        """
        if not self._srf_token:
            raise ValueError("Not authenticated")

        thumb_param = 1 if thumbnail else 0
        timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)

        try:
            async with self._session.get(
                f"{BASE_URL}/GetCmd",
                params={
                    "cmd": "PhotoGet",
                    "id": photo_id,
                    "thumb": thumb_param,
                },
                headers=self._headers,
                timeout=timeout,
            ) as response:
                if response.status == 200:
                    photo_data = await response.read()
                    _LOGGER.debug("Retrieved photo %s, size: %d bytes", photo_id, len(photo_data))
                    return photo_data
                else:
                    _LOGGER.error("Error retrieving photo %s. Status: %s", photo_id, response.status)
                    return None

        except (aiohttp.ClientError, ValueError) as err:
            _LOGGER.error("Failed to get photo %s: %s", photo_id, err)
            return None