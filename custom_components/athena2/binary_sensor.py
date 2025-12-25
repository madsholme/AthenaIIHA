"""Binary sensor platform for Athena II integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL,
)
from .coordinator import Athena2Coordinator


@dataclass(frozen=True)
class Athena2BinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Athena II binary sensor entity."""

    value_fn: Callable[[dict[str, Any]], bool] | None = None


BINARY_SENSOR_DESCRIPTIONS: tuple[Athena2BinarySensorEntityDescription, ...] = (
    Athena2BinarySensorEntityDescription(
        key="printing",
        name="Printing",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:printer-3d-nozzle",
        value_fn=lambda data: data.get("Printing", False),
    ),
    Athena2BinarySensorEntityDescription(
        key="paused",
        name="Paused",
        icon="mdi:pause",
        value_fn=lambda data: data.get("Paused", False),
    ),
    Athena2BinarySensorEntityDescription(
        key="halted",
        name="Halted",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:stop-circle",
        value_fn=lambda data: data.get("Halted", False),
    ),
    Athena2BinarySensorEntityDescription(
        key="panicked",
        name="Panicked",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:alert-circle",
        value_fn=lambda data: data.get("Panicked", False),
    ),
    Athena2BinarySensorEntityDescription(
        key="force_stop",
        name="Force Stop",
        icon="mdi:hand-back-right",
        value_fn=lambda data: data.get("ForceStop", False),
    ),
    Athena2BinarySensorEntityDescription(
        key="auto_shutdown",
        name="Auto Shutdown",
        icon="mdi:power",
        value_fn=lambda data: data.get("AutoShutdown", False),
    ),
    Athena2BinarySensorEntityDescription(
        key="covered",
        name="Covered",
        device_class=BinarySensorDeviceClass.DOOR,
        icon="mdi:inbox",
        value_fn=lambda data: data.get("Covered", False),
    ),
    Athena2BinarySensorEntityDescription(
        key="cast",
        name="Cast",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:cast",
        value_fn=lambda data: data.get("Cast", False),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Athena II binary sensor based on a config entry."""
    coordinator: Athena2Coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        Athena2BinarySensor(coordinator, entry, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class Athena2BinarySensor(CoordinatorEntity[Athena2Coordinator], BinarySensorEntity):
    """Representation of an Athena II binary sensor."""

    entity_description: Athena2BinarySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: Athena2Coordinator,
        entry: ConfigEntry,
        description: Athena2BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Athena II ({coordinator.host})",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "sw_version": coordinator.data.get("Version") if coordinator.data else None,
        }

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        if self.entity_description.value_fn is not None:
            return self.entity_description.value_fn(self.coordinator.data)
        return False
