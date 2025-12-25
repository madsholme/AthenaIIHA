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

                # Extract first frame from MJPEG stream
                image_data = await self._extract_mjpeg_frame(response)

                if not image_data:
                    _LOGGER.warning("No image data extracted from MJPEG stream")
                    return None

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

    async def _extract_mjpeg_frame(self, response: aiohttp.ClientResponse) -> bytes | None:
        """Extract a single frame from MJPEG stream."""
        try:
            # MJPEG streams use multipart/x-mixed-replace with boundary markers
            boundary = None
            content_type = response.headers.get("Content-Type", "")

            # Extract boundary from content type
            if "boundary=" in content_type:
                boundary = content_type.split("boundary=")[-1].strip()
                boundary = f"--{boundary}".encode()
            else:
                # Common default boundary
                boundary = b"--myboundary"

            # Read stream until we find a complete JPEG frame
            buffer = b""
            async for chunk in response.content.iter_chunked(1024):
                buffer += chunk

                # Look for JPEG start (FFD8) and end (FFD9) markers
                jpeg_start = buffer.find(b"\xff\xd8")
                if jpeg_start != -1:
                    jpeg_end = buffer.find(b"\xff\xd9", jpeg_start)
                    if jpeg_end != -1:
                        # Extract complete JPEG frame
                        return buffer[jpeg_start:jpeg_end + 2]

                # Prevent buffer from growing too large
                if len(buffer) > 1024 * 1024:  # 1MB limit
                    break

            return None

        except Exception as err:
            _LOGGER.error("Error extracting MJPEG frame: %s", err)
            return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._coordinator.last_update_success
