"""Camera platform for Athena II integration."""
from __future__ import annotations

import asyncio
from datetime import datetime
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
    CONF_CAMERA_FPS,
    DEFAULT_CAMERA_FPS,
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

    # Get camera FPS from options or config
    camera_fps = entry.options.get(
        CONF_CAMERA_FPS,
        entry.data.get(CONF_CAMERA_FPS, DEFAULT_CAMERA_FPS),
    )

    async_add_entities([Athena2Camera(coordinator, entry, session, camera_fps)])


class Athena2Camera(Camera):
    """Representation of an Athena II camera with 90° clockwise rotation."""

    _attr_has_entity_name = True
    _attr_name = "Camera"

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        session: aiohttp.ClientSession,
        camera_fps: float,
    ) -> None:
        """Initialize the camera."""
        super().__init__()
        self._coordinator = coordinator
        self._session = session
        self._camera_fps = camera_fps
        self._frame_interval = 1.0 / camera_fps  # Time between frames in seconds
        self._last_frame_time = 0
        self._last_image = None
        self._attr_unique_id = f"{entry.entry_id}_camera"
        self._stream_url = f"http://{coordinator.host}:{coordinator.port}{ENDPOINT_CAMERA}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Athena II ({coordinator.host})",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "sw_version": coordinator.data.get("Version") if coordinator.data else None,
        }
        self._attr_frame_interval = self._frame_interval

        _LOGGER.info(
            "Camera initialized with %.1f FPS (frame every %.1f seconds)",
            camera_fps,
            self._frame_interval,
        )

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a rotated camera image with rate limiting."""
        current_time = datetime.now().timestamp()

        # Check if enough time has passed since last frame
        time_since_last_frame = current_time - self._last_frame_time

        if time_since_last_frame < self._frame_interval and self._last_image is not None:
            # Return cached image if we're fetching too fast
            _LOGGER.debug(
                "Returning cached image (%.2fs since last fetch, interval is %.2fs)",
                time_since_last_frame,
                self._frame_interval,
            )
            return self._last_image

        try:
            async with async_timeout.timeout(15):
                response = await self._session.get(self._stream_url)
                response.raise_for_status()

                # Extract first frame from MJPEG stream
                image_data = await self._extract_mjpeg_frame(response)

                if not image_data:
                    _LOGGER.warning("No image data extracted from MJPEG stream")
                    return self._last_image  # Return cached image on failure

                _LOGGER.debug("Processing JPEG image of %d bytes", len(image_data))

                # Rotate image 90° clockwise
                image = Image.open(io.BytesIO(image_data))
                rotated = image.rotate(-90, expand=True)  # -90 = clockwise rotation

                # Convert back to bytes
                output = io.BytesIO()
                rotated.save(output, format="JPEG", quality=85)
                rotated_bytes = output.getvalue()

                # Cache the image and timestamp
                self._last_image = rotated_bytes
                self._last_frame_time = current_time

                return rotated_bytes

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout getting camera image from %s", self._stream_url)
            return self._last_image  # Return cached image on timeout
        except aiohttp.ClientError as err:
            _LOGGER.error("Error getting camera image: %s", err)
            return self._last_image
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("Unexpected error processing camera image: %s", err)
            return self._last_image

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
