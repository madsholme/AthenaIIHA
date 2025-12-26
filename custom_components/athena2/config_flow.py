"""Config flow for Athena II integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_CAMERA_FPS,
    CONF_SCAN_INTERVAL,
    DEFAULT_CAMERA_FPS,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ENDPOINT_STATUS,
    MAX_CAMERA_FPS,
    MAX_SCAN_INTERVAL,
    MIN_CAMERA_FPS,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


async def validate_connection(
    hass: HomeAssistant, host: str, port: int
) -> dict[str, Any]:
    """Validate the connection to the printer."""
    session = async_get_clientsession(hass)
    url = f"http://{host}:{port}{ENDPOINT_STATUS}"

    try:
        async with async_timeout.timeout(10):
            response = await session.get(url)
            response.raise_for_status()
            data = await response.json()

            # Validate essential fields
            if "Status" not in data:
                raise ValueError("Invalid response from printer")

            return {
                "hostname": data.get("Hostname", "Unknown"),
                "version": data.get("Version", "Unknown"),
            }

    except asyncio.TimeoutError as err:
        raise CannotConnect("Timeout connecting to printer") from err
    except aiohttp.ClientError as err:
        raise CannotConnect(f"Cannot connect to printer: {err}") from err
    except ValueError as err:
        raise InvalidData(f"Invalid data from printer: {err}") from err


class Athena2ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Athena II."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_connection(
                    self.hass,
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                )

                # Set unique ID based on host to prevent duplicates
                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Athena II ({user_input[CONF_HOST]})",
                    data=user_input,
                )

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidData:
                errors["base"] = "invalid_data"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=DEFAULT_SCAN_INTERVAL,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    ),
                    vol.Optional(
                        CONF_CAMERA_FPS,
                        default=DEFAULT_CAMERA_FPS,
                    ): vol.All(
                        vol.Coerce(float),
                        vol.Range(min=MIN_CAMERA_FPS, max=MAX_CAMERA_FPS),
                    ),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> Athena2OptionsFlowHandler:
        """Get the options flow for this handler."""
        return Athena2OptionsFlowHandler(config_entry)


class Athena2OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Athena II."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL,
                            self.config_entry.data.get(
                                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                            ),
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    ),
                    vol.Optional(
                        CONF_CAMERA_FPS,
                        default=self.config_entry.options.get(
                            CONF_CAMERA_FPS,
                            self.config_entry.data.get(
                                CONF_CAMERA_FPS, DEFAULT_CAMERA_FPS
                            ),
                        ),
                    ): vol.All(
                        vol.Coerce(float),
                        vol.Range(min=MIN_CAMERA_FPS, max=MAX_CAMERA_FPS),
                    ),
                }
            ),
        )


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidData(Exception):
    """Error to indicate there is invalid data."""
