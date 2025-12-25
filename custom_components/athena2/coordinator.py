"""DataUpdateCoordinator for Athena II printer."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import ANALYTIC_METRICS, ENDPOINT_ANALYTIC_VALUE, ENDPOINT_STATUS

_LOGGER = logging.getLogger(__name__)


class Athena2Coordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Athena II data from the printer."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        scan_interval: int,
    ) -> None:
        """Initialize the coordinator."""
        self.host = host
        self.port = port
        self._session = session
        self._status_url = f"http://{host}:{port}{ENDPOINT_STATUS}"

        super().__init__(
            hass,
            _LOGGER,
            name="Athena II",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the printer."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.get(self._status_url)
                response.raise_for_status()
                data = await response.json()

                # Validate that we have essential data
                if "Status" not in data:
                    raise UpdateFailed("Invalid response from printer - missing Status field")

                # Fetch analytic data
                analytic_data = await self._fetch_analytic_data()
                data.update(analytic_data)

                # Parse and normalize data
                normalized_data = self._normalize_data(data)

                return normalized_data

        except asyncio.TimeoutError as err:
            raise UpdateFailed(f"Timeout communicating with printer at {self.host}") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with printer at {self.host}: {err}") from err
        except ValueError as err:
            raise UpdateFailed(f"Invalid JSON response from printer at {self.host}") from err

    async def _fetch_analytic_data(self) -> dict[str, Any]:
        """Fetch analytic sensor values."""
        analytic_data = {}

        try:
            # Fetch all analytic metrics in parallel
            for metric_id, metric_key in ANALYTIC_METRICS.items():
                url = f"http://{self.host}:{self.port}{ENDPOINT_ANALYTIC_VALUE}/{metric_id}"
                try:
                    async with async_timeout.timeout(5):
                        response = await self._session.get(url)
                        if response.status == 200:
                            value = await response.text()
                            try:
                                analytic_data[metric_key] = float(value.strip())
                            except ValueError:
                                _LOGGER.debug("Could not parse analytic value for %s: %s", metric_key, value)
                except (asyncio.TimeoutError, aiohttp.ClientError) as err:
                    _LOGGER.debug("Error fetching analytic metric %s: %s", metric_key, err)
                    continue
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.warning("Error fetching analytic data: %s", err)

        return analytic_data

    def _normalize_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Normalize and convert units in the data."""
        normalized = data.copy()

        # Parse percentage strings (e.g., "49%" -> 49)
        for key in ["disk", "mem", "proc"]:
            if key in normalized and isinstance(normalized[key], str):
                try:
                    normalized[key] = float(normalized[key].rstrip("%"))
                except (ValueError, AttributeError):
                    _LOGGER.warning("Could not parse percentage value for %s: %s", key, normalized[key])

        # Parse temperature string (e.g., "41.35°C" -> 41.35)
        if "temp" in normalized and isinstance(normalized["temp"], str):
            try:
                normalized["temp"] = float(normalized["temp"].rstrip("°C"))
            except (ValueError, AttributeError):
                _LOGGER.warning("Could not parse temperature value: %s", normalized["temp"])

        # Convert CurrentHeight from micrometers to millimeters
        if "CurrentHeight" in normalized and isinstance(normalized["CurrentHeight"], (int, float)):
            normalized["CurrentHeight"] = normalized["CurrentHeight"] / 1000.0

        return normalized
