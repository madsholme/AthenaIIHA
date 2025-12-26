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
            async with async_timeout.timeout(15):
                response = await self._session.get(self._stream_url)
                response.raise_for_status()

                # Extract first frame from MJPEG stream
                image_data = await self._extract_mjpeg_frame(response)

                if not image_data:
                    _LOGGER.warning("No image data extracted from MJPEG stream")
                    return None

                _LOGGER.debug("Processing JPEG image of %d bytes", len(image_data))

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
            # Read stream until we find a complete JPEG frame
            buffer = b""
            content_length = None
            in_jpeg = False

            async for chunk in response.content.iter_chunked(4096):
                buffer += chunk

                # Look for Content-Length header in stream
                if not in_jpeg and b"Content-Length:" in buffer:
                    try:
                        length_line = buffer.split(b"Content-Length:")[1].split(b"\r\n")[0]
                        content_length = int(length_line.strip())
                    except (ValueError, IndexError):
                        pass

                # Look for JPEG start (FFD8) marker
                if not in_jpeg:
                    jpeg_start = buffer.find(b"\xff\xd8")
                    if jpeg_start != -1:
                        in_jpeg = True
                        # Keep only from JPEG start
                        buffer = buffer[jpeg_start:]

                # Look for JPEG end (FFD9) marker
                if in_jpeg:
                    jpeg_end = buffer.find(b"\xff\xd9")
                    if jpeg_end != -1:
                        # Extract complete JPEG frame (including FFD9 marker)
                        jpeg_data = buffer[:jpeg_end + 2]
                        _LOGGER.debug("Extracted JPEG frame of %d bytes", len(jpeg_data))
                        return jpeg_data

                # Safety check: if we have content length and buffer is big enough
                if content_length and len(buffer) >= content_length + 1000:
                    # Should have found end marker by now, try to extract what we have
                    jpeg_end = buffer.find(b"\xff\xd9")
                    if jpeg_end != -1:
                        return buffer[:jpeg_end + 2]

                # Prevent buffer from growing too large
                if len(buffer) > 2 * 1024 * 1024:  # 2MB limit
                    _LOGGER.warning("Buffer exceeded 2MB without finding complete frame")
                    break

            return None

        except Exception as err:
            _LOGGER.error("Error extracting MJPEG frame: %s", err)
            return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._coordinator.last_update_success
