"""Camera platform for Athena II integration."""
from __future__ import annotations

import asyncio
import io
import logging

import aiohttp
import async_timeout
from PIL import Image

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    ENDPOINT_CAMERA,
    MANUFACTURER,
    MODEL,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Athena II camera based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    session = async_get_clientsession(hass)

    async_add_entities([Athena2Camera(coordinator, entry, session)])


class Athena2Camera(Camera):
    """Representation of an Athena II camera with 90° clockwise rotation."""

    _attr_has_entity_name = True
    _attr_name = "Camera"

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the camera."""
        super().__init__()
        self._coordinator = coordinator
        self._session = session
        self._attr_unique_id = f"{entry.entry_id}_camera"
        self._stream_url = f"http://{coordinator.host}:{coordinator.port}{ENDPOINT_CAMERA}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Athena II ({coordinator.host})",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "sw_version": coordinator.data.get("Version") if coordinator.data else None,
        }

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a rotated camera image."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.get(self._stream_url)
                response.raise_for_status()
                image_data = await response.read()

                # Rotate image 90° clockwise
                image = Image.open(io.BytesIO(image_data))
                rotated = image.rotate(-90, expand=True)  # -90 = clockwise rotation

                # Convert back to bytes
                output = io.BytesIO()
                rotated.save(output, format="JPEG", quality=85)
                return output.getvalue()

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout getting camera image from %s", self._stream_url)
            return None
        except aiohttp.ClientError as err:
            _LOGGER.error("Error getting camera image: %s", err)
            return None
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("Unexpected error processing camera image: %s", err)
            return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._coordinator.last_update_success
