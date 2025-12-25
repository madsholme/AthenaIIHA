"""Sensor platform for Athena II integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfLength,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL,
)
from .coordinator import Athena2Coordinator


@dataclass(frozen=True)
class Athena2SensorEntityDescription(SensorEntityDescription):
    """Describes Athena II sensor entity."""

    value_fn: Callable[[dict[str, Any]], StateType] | None = None
    attr_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


SENSOR_DESCRIPTIONS: tuple[Athena2SensorEntityDescription, ...] = (
    # Print status sensors
    Athena2SensorEntityDescription(
        key="status",
        name="Status",
        icon="mdi:printer-3d",
        value_fn=lambda data: data.get("Status"),
    ),
    Athena2SensorEntityDescription(
        key="current_layer",
        name="Current Layer",
        icon="mdi:layers",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("LayerID"),
    ),
    Athena2SensorEntityDescription(
        key="total_layers",
        name="Total Layers",
        icon="mdi:layers-triple",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("LayersCount"),
    ),
    Athena2SensorEntityDescription(
        key="print_progress",
        name="Print Progress",
        icon="mdi:progress-clock",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: (
            round((data.get("LayerID", 0) / data.get("LayersCount", 1)) * 100, 1)
            if data.get("LayersCount", 0) > 0 and data.get("Printing", False)
            else 0
        ),
        attr_fn=lambda data: {
            "current_layer": data.get("LayerID"),
            "total_layers": data.get("LayersCount"),
            "print_file": data.get("Path"),
        },
    ),
    # Height sensors
    Athena2SensorEntityDescription(
        key="current_height",
        name="Current Height",
        icon="mdi:arrow-up-bold",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("CurrentHeight"),
    ),
    Athena2SensorEntityDescription(
        key="plate_height",
        name="Plate Height",
        icon="mdi:arrow-collapse-down",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("PlateHeight"),
    ),
    # Timing sensors
    Athena2SensorEntityDescription(
        key="layer_time",
        name="Layer Time",
        icon="mdi:timer",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("LayerTime"),
    ),
    Athena2SensorEntityDescription(
        key="prev_layer_time",
        name="Previous Layer Time",
        icon="mdi:timer-outline",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("PrevLayerTime"),
    ),
    Athena2SensorEntityDescription(
        key="estimated_time_remaining",
        name="Estimated Time Remaining",
        icon="mdi:clock-end",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: (
            (data.get("LayersCount", 0) - data.get("LayerID", 0)) * data.get("LayerTime", 0)
            if data.get("Printing", False) and data.get("LayerTime", 0) > 0
            else None
        ),
    ),
    # Temperature sensors
    Athena2SensorEntityDescription(
        key="system_temp",
        name="System Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("temp"),
    ),
    Athena2SensorEntityDescription(
        key="mcu_temp",
        name="MCU Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("mcu"),
    ),
    Athena2SensorEntityDescription(
        key="resin_temp",
        name="Resin Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("resin"),
    ),
    # Fan sensors
    Athena2SensorEntityDescription(
        key="mcu_fan_rpm",
        name="MCU Fan Speed",
        icon="mdi:fan",
        native_unit_of_measurement="RPM",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("mcu_fan_rpm"),
    ),
    Athena2SensorEntityDescription(
        key="uv_fan_rpm",
        name="UV Fan Speed",
        icon="mdi:fan",
        native_unit_of_measurement="RPM",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("uv_fan_rpm"),
    ),
    # Resin and lamp sensors
    Athena2SensorEntityDescription(
        key="resin_level",
        name="Resin Level",
        icon="mdi:cup-water",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("ResinLevelMm"),
    ),
    Athena2SensorEntityDescription(
        key="lamp_hours",
        name="Lamp Hours",
        icon="mdi:lightbulb-on",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.get("LampHours"),
    ),
    # System resource sensors
    Athena2SensorEntityDescription(
        key="disk_usage",
        name="Disk Usage",
        icon="mdi:harddisk",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("disk"),
    ),
    Athena2SensorEntityDescription(
        key="memory_usage",
        name="Memory Usage",
        icon="mdi:memory",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("mem"),
    ),
    Athena2SensorEntityDescription(
        key="cpu_usage",
        name="CPU Usage",
        icon="mdi:chip",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("proc"),
    ),
    Athena2SensorEntityDescription(
        key="process_count",
        name="Process Count",
        icon="mdi:application-cog",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("proc_numb"),
    ),
    # System info sensors
    Athena2SensorEntityDescription(
        key="uptime",
        name="Uptime",
        icon="mdi:clock-outline",
        value_fn=lambda data: data.get("uptime"),
    ),
    Athena2SensorEntityDescription(
        key="hostname",
        name="Hostname",
        icon="mdi:network",
        value_fn=lambda data: data.get("Hostname"),
    ),
    Athena2SensorEntityDescription(
        key="ip_address",
        name="IP Address",
        icon="mdi:ip-network",
        value_fn=lambda data: data.get("IP"),
    ),
    Athena2SensorEntityDescription(
        key="firmware_version",
        name="Firmware Version",
        icon="mdi:package-variant",
        value_fn=lambda data: data.get("Version"),
    ),
    Athena2SensorEntityDescription(
        key="wifi",
        name="WiFi",
        icon="mdi:wifi",
        value_fn=lambda data: data.get("Wifi"),
    ),
    # Analytic sensors from /analytic/value endpoint
    Athena2SensorEntityDescription(
        key="pressure",
        name="Pressure",
        icon="mdi:gauge",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("pressure"),
    ),
    Athena2SensorEntityDescription(
        key="temperature_vat",
        name="Vat Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("temperature_vat"),
    ),
    Athena2SensorEntityDescription(
        key="temperature_vat_target",
        name="Vat Temperature Target",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("temperature_vat_target"),
    ),
    Athena2SensorEntityDescription(
        key="temperature_chamber",
        name="Chamber Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("temperature_chamber"),
    ),
    Athena2SensorEntityDescription(
        key="temperature_chamber_target",
        name="Chamber Temperature Target",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("temperature_chamber_target"),
    ),
    Athena2SensorEntityDescription(
        key="temperature_inside",
        name="Inside Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("temperature_inside"),
    ),
    Athena2SensorEntityDescription(
        key="temperature_inside_target",
        name="Inside Temperature Target",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("temperature_inside_target"),
    ),
    Athena2SensorEntityDescription(
        key="temperature_outside",
        name="Outside Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("temperature_outside"),
    ),
    Athena2SensorEntityDescription(
        key="temperature_outside_target",
        name="Outside Temperature Target",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("temperature_outside_target"),
    ),
    Athena2SensorEntityDescription(
        key="temperature_ptc",
        name="PTC Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("temperature_ptc"),
    ),
    Athena2SensorEntityDescription(
        key="temperature_ptc_target",
        name="PTC Temperature Target",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("temperature_ptc_target"),
    ),
    Athena2SensorEntityDescription(
        key="ptc_fan_rpm",
        name="PTC Fan Speed",
        icon="mdi:fan",
        native_unit_of_measurement="RPM",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("ptc_fan_rpm"),
    ),
    Athena2SensorEntityDescription(
        key="aegis_fan_rpm",
        name="AEGIS Fan Speed",
        icon="mdi:fan",
        native_unit_of_measurement="RPM",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("aegis_fan_rpm"),
    ),
    Athena2SensorEntityDescription(
        key="voc_inlet",
        name="VOC Inlet",
        icon="mdi:air-filter",
        native_unit_of_measurement="PPM",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("voc_inlet"),
    ),
    Athena2SensorEntityDescription(
        key="voc_outlet",
        name="VOC Outlet",
        icon="mdi:air-filter",
        native_unit_of_measurement="PPM",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("voc_outlet"),
    ),
    Athena2SensorEntityDescription(
        key="lift_height",
        name="Lift Height",
        icon="mdi:arrow-expand-vertical",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("lift_height"),
    ),
    Athena2SensorEntityDescription(
        key="dynamic_wait",
        name="Dynamic Wait",
        icon="mdi:timer-sand",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("dynamic_wait"),
    ),
    Athena2SensorEntityDescription(
        key="cure",
        name="Cure Time",
        icon="mdi:timer",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("cure"),
    ),
    Athena2SensorEntityDescription(
        key="speed",
        name="Speed",
        icon="mdi:speedometer",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("speed"),
    ),
    Athena2SensorEntityDescription(
        key="solid_area",
        name="Solid Area",
        icon="mdi:square",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("solid_area"),
    ),
    Athena2SensorEntityDescription(
        key="area_count",
        name="Area Count",
        icon="mdi:counter",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("area_count"),
    ),
    Athena2SensorEntityDescription(
        key="largest_area",
        name="Largest Area",
        icon="mdi:resize",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("largest_area"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Athena II sensor based on a config entry."""
    coordinator: Athena2Coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        Athena2Sensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


class Athena2Sensor(CoordinatorEntity[Athena2Coordinator], SensorEntity):
    """Representation of an Athena II sensor."""

    entity_description: Athena2SensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: Athena2Coordinator,
        entry: ConfigEntry,
        description: Athena2SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
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
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if self.entity_description.value_fn is not None:
            return self.entity_description.value_fn(self.coordinator.data)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional attributes."""
        if self.entity_description.attr_fn is not None:
            return self.entity_description.attr_fn(self.coordinator.data)
        return None
