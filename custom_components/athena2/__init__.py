"""The Athena II integration."""
from __future__ import annotations

import asyncio
import logging

import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ENDPOINT_AUTO_SHUTDOWN_DISABLE,
    ENDPOINT_AUTO_SHUTDOWN_ENABLE,
    ENDPOINT_PAUSE,
    ENDPOINT_REBOOT,
    ENDPOINT_SHUTDOWN,
    ENDPOINT_START_PRINT,
    ENDPOINT_STOP,
    ENDPOINT_UNPAUSE,
    SERVICE_CANCEL_PRINT,
    SERVICE_PAUSE_PRINT,
    SERVICE_REBOOT,
    SERVICE_RESUME_PRINT,
    SERVICE_SET_AUTO_SHUTDOWN,
    SERVICE_SHUTDOWN,
    SERVICE_START_PRINT,
)
from .coordinator import Athena2Coordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.CAMERA,
]


def _get_coordinator_from_call(hass: HomeAssistant, call: ServiceCall) -> Athena2Coordinator:
    """Extract coordinator from service call target."""
    # Services use entity targeting, extract device/entry from first entity
    entity_id = call.data.get("entity_id")
    if isinstance(entity_id, list) and entity_id:
        entity_id = entity_id[0]

    if not entity_id:
        raise HomeAssistantError("No entity specified for service call")

    # Get entry_id from entity registry
    entity_reg = entity_registry.async_get(hass)
    entity_entry = entity_reg.async_get(entity_id)

    if not entity_entry:
        raise HomeAssistantError(f"Entity {entity_id} not found")

    if entity_entry.config_entry_id not in hass.data.get(DOMAIN, {}):
        raise HomeAssistantError("Athena II device not found")

    return hass.data[DOMAIN][entity_entry.config_entry_id]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Athena II from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, 80)
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )

    session = async_get_clientsession(hass)

    coordinator = Athena2Coordinator(
        hass=hass,
        session=session,
        host=host,
        port=port,
        scan_interval=scan_interval,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services (only once, shared across all devices)
    async def async_pause_print(call: ServiceCall) -> None:
        """Handle pause print service call."""
        coordinator = _get_coordinator_from_call(hass, call)
        url = f"http://{coordinator.host}:{coordinator.port}{ENDPOINT_PAUSE}"

        try:
            async with async_timeout.timeout(10):
                response = await coordinator.session.get(url)
                response.raise_for_status()
                _LOGGER.info("Print paused successfully")
                await coordinator.async_request_refresh()
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout pausing print")
            raise HomeAssistantError("Timeout connecting to printer")
        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to pause print: %s", err)
            raise HomeAssistantError(f"Failed to pause print: {err}")

    async def async_resume_print(call: ServiceCall) -> None:
        """Handle resume print service call."""
        coordinator = _get_coordinator_from_call(hass, call)
        url = f"http://{coordinator.host}:{coordinator.port}{ENDPOINT_UNPAUSE}"

        try:
            async with async_timeout.timeout(10):
                response = await coordinator.session.get(url)
                response.raise_for_status()
                _LOGGER.info("Print resumed successfully")
                await coordinator.async_request_refresh()
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout resuming print")
            raise HomeAssistantError("Timeout connecting to printer")
        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to resume print: %s", err)
            raise HomeAssistantError(f"Failed to resume print: {err}")

    async def async_cancel_print(call: ServiceCall) -> None:
        """Handle cancel print service call."""
        coordinator = _get_coordinator_from_call(hass, call)
        url = f"http://{coordinator.host}:{coordinator.port}{ENDPOINT_STOP}"

        try:
            async with async_timeout.timeout(10):
                response = await coordinator.session.get(url)
                response.raise_for_status()
                _LOGGER.info("Print cancelled successfully")
                await coordinator.async_request_refresh()
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout cancelling print")
            raise HomeAssistantError("Timeout connecting to printer")
        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to cancel print: %s", err)
            raise HomeAssistantError(f"Failed to cancel print: {err}")

    async def async_set_auto_shutdown(call: ServiceCall) -> None:
        """Handle set auto shutdown service call."""
        coordinator = _get_coordinator_from_call(hass, call)
        enabled = call.data.get("enabled", False)
        endpoint = ENDPOINT_AUTO_SHUTDOWN_ENABLE if enabled else ENDPOINT_AUTO_SHUTDOWN_DISABLE
        url = f"http://{coordinator.host}:{coordinator.port}{endpoint}"

        try:
            async with async_timeout.timeout(10):
                response = await coordinator.session.get(url)
                response.raise_for_status()
                _LOGGER.info("Auto shutdown %s successfully", "enabled" if enabled else "disabled")
                await coordinator.async_request_refresh()
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout setting auto shutdown")
            raise HomeAssistantError("Timeout connecting to printer")
        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to set auto shutdown: %s", err)
            raise HomeAssistantError(f"Failed to set auto shutdown: {err}")

    async def async_start_print(call: ServiceCall) -> None:
        """Handle start print service call."""
        coordinator = _get_coordinator_from_call(hass, call)
        plate_id = call.data.get("plate_id")
        if not plate_id:
            raise HomeAssistantError("plate_id parameter is required")

        url = f"http://{coordinator.host}:{coordinator.port}{ENDPOINT_START_PRINT}{plate_id}"

        try:
            async with async_timeout.timeout(10):
                response = await coordinator.session.get(url)
                response.raise_for_status()
                _LOGGER.info("Print started successfully for plate_id: %s", plate_id)
                await coordinator.async_request_refresh()
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout starting print")
            raise HomeAssistantError("Timeout connecting to printer")
        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to start print: %s", err)
            raise HomeAssistantError(f"Failed to start print: {err}")

    async def async_shutdown(call: ServiceCall) -> None:
        """Handle shutdown service call."""
        coordinator = _get_coordinator_from_call(hass, call)
        url = f"http://{coordinator.host}:{coordinator.port}{ENDPOINT_SHUTDOWN}"

        try:
            async with async_timeout.timeout(10):
                response = await coordinator.session.get(url)
                response.raise_for_status()
                _LOGGER.info("Printer shutdown initiated successfully")
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout shutting down printer")
            raise HomeAssistantError("Timeout connecting to printer")
        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to shutdown printer: %s", err)
            raise HomeAssistantError(f"Failed to shutdown printer: {err}")

    async def async_reboot(call: ServiceCall) -> None:
        """Handle reboot service call."""
        coordinator = _get_coordinator_from_call(hass, call)
        url = f"http://{coordinator.host}:{coordinator.port}{ENDPOINT_REBOOT}"

        try:
            async with async_timeout.timeout(10):
                response = await coordinator.session.get(url)
                response.raise_for_status()
                _LOGGER.info("Printer reboot initiated successfully")
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout rebooting printer")
            raise HomeAssistantError("Timeout connecting to printer")
        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to reboot printer: %s", err)
            raise HomeAssistantError(f"Failed to reboot printer: {err}")

    # Register services only if not already registered
    if not hass.services.has_service(DOMAIN, SERVICE_PAUSE_PRINT):
        hass.services.async_register(DOMAIN, SERVICE_PAUSE_PRINT, async_pause_print)
    if not hass.services.has_service(DOMAIN, SERVICE_RESUME_PRINT):
        hass.services.async_register(DOMAIN, SERVICE_RESUME_PRINT, async_resume_print)
    if not hass.services.has_service(DOMAIN, SERVICE_CANCEL_PRINT):
        hass.services.async_register(DOMAIN, SERVICE_CANCEL_PRINT, async_cancel_print)
    if not hass.services.has_service(DOMAIN, SERVICE_SET_AUTO_SHUTDOWN):
        hass.services.async_register(DOMAIN, SERVICE_SET_AUTO_SHUTDOWN, async_set_auto_shutdown)
    if not hass.services.has_service(DOMAIN, SERVICE_START_PRINT):
        hass.services.async_register(DOMAIN, SERVICE_START_PRINT, async_start_print)
    if not hass.services.has_service(DOMAIN, SERVICE_SHUTDOWN):
        hass.services.async_register(DOMAIN, SERVICE_SHUTDOWN, async_shutdown)
    if not hass.services.has_service(DOMAIN, SERVICE_REBOOT):
        hass.services.async_register(DOMAIN, SERVICE_REBOOT, async_reboot)

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

        # Unregister services only if this is the last Athena II device
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_PAUSE_PRINT)
            hass.services.async_remove(DOMAIN, SERVICE_RESUME_PRINT)
            hass.services.async_remove(DOMAIN, SERVICE_CANCEL_PRINT)
            hass.services.async_remove(DOMAIN, SERVICE_SET_AUTO_SHUTDOWN)
            hass.services.async_remove(DOMAIN, SERVICE_START_PRINT)
            hass.services.async_remove(DOMAIN, SERVICE_SHUTDOWN)
            hass.services.async_remove(DOMAIN, SERVICE_REBOOT)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
