"""Constants for the Athena II integration."""
from typing import Final

DOMAIN: Final = "athena2"

# Configuration constants
CONF_HOST: Final = "host"
CONF_PORT: Final = "port"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_CAMERA_FPS: Final = "camera_fps"

# Defaults
DEFAULT_PORT: Final = 80
DEFAULT_SCAN_INTERVAL: Final = 30
MIN_SCAN_INTERVAL: Final = 10
MAX_SCAN_INTERVAL: Final = 300
DEFAULT_CAMERA_FPS: Final = 1  # 1 frame every 10 seconds
MIN_CAMERA_FPS: Final = 0.1  # 1 frame every 10 seconds
MAX_CAMERA_FPS: Final = 5  # 5 frames per second (near real-time)

# Platforms
PLATFORMS: Final = ["sensor", "binary_sensor", "camera"]

# Services
SERVICE_PAUSE_PRINT: Final = "pause_print"
SERVICE_RESUME_PRINT: Final = "resume_print"
SERVICE_CANCEL_PRINT: Final = "cancel_print"
SERVICE_SET_AUTO_SHUTDOWN: Final = "set_auto_shutdown"
SERVICE_START_PRINT: Final = "start_print"
SERVICE_SHUTDOWN: Final = "shutdown"
SERVICE_REBOOT: Final = "reboot"

# API Endpoints
ENDPOINT_STATUS: Final = "/status"
ENDPOINT_CAMERA: Final = "/athena-camera/stream"
ENDPOINT_ANALYTIC_VALUE: Final = "/analytic/value"
ENDPOINT_PAUSE: Final = "/printer/pause"
ENDPOINT_UNPAUSE: Final = "/printer/unpause"
ENDPOINT_STOP: Final = "/printer/stop"
ENDPOINT_AUTO_SHUTDOWN_ENABLE: Final = "/printer/auto-shutdown/enable"
ENDPOINT_AUTO_SHUTDOWN_DISABLE: Final = "/printer/auto-shutdown/disable"
ENDPOINT_START_PRINT: Final = "/printer/start/"
ENDPOINT_SHUTDOWN: Final = "/printer/off"
ENDPOINT_REBOOT: Final = "/printer/restart"

# Analytic metric IDs mapping to keys
ANALYTIC_METRICS: Final = {
    0: "layer_height",
    1: "solid_area",
    2: "area_count",
    3: "largest_area",
    4: "speed",
    5: "cure",
    6: "pressure",
    7: "temperature_inside",
    8: "temperature_outside",
    9: "layer_time_analytic",
    10: "lift_height",
    11: "temperature_mcu_analytic",
    12: "temperature_inside_target",
    13: "temperature_outside_target",
    14: "temperature_mcu_target",
    15: "mcu_fan_rpm_analytic",
    16: "uv_fan_rpm_analytic",
    17: "dynamic_wait",
    18: "temperature_vat",
    19: "temperature_vat_target",
    20: "ptc_fan_rpm",
    21: "aegis_fan_rpm",
    22: "temperature_chamber",
    23: "temperature_chamber_target",
    24: "temperature_ptc",
    25: "temperature_ptc_target",
    26: "voc_inlet",
    27: "voc_outlet",
}

# Sensor keys from API
SENSOR_STATUS: Final = "Status"
SENSOR_STATE: Final = "State"
SENSOR_CURRENT_HEIGHT: Final = "CurrentHeight"
SENSOR_LAYER_ID: Final = "LayerID"
SENSOR_LAYERS_COUNT: Final = "LayersCount"
SENSOR_LAYER_SINCE_START: Final = "LayerSinceStart"
SENSOR_LAYER_TIME: Final = "LayerTime"
SENSOR_PREV_LAYER_TIME: Final = "PrevLayerTime"
SENSOR_LAYER_START_TIME: Final = "LayerStartTime"
SENSOR_PLATE_HEIGHT: Final = "PlateHeight"
SENSOR_PATH: Final = "Path"
SENSOR_STARTED: Final = "started"
SENSOR_LAYER_TIME_ALT: Final = "layer_time"
SENSOR_UPTIME: Final = "uptime"
SENSOR_TEMP: Final = "temp"
SENSOR_MCU: Final = "mcu"
SENSOR_RESIN: Final = "resin"
SENSOR_MCU_FAN_RPM: Final = "mcu_fan_rpm"
SENSOR_UV_FAN_RPM: Final = "uv_fan_rpm"
SENSOR_RESIN_LEVEL_MM: Final = "ResinLevelMm"
SENSOR_LAMP_HOURS: Final = "LampHours"
SENSOR_HOSTNAME: Final = "Hostname"
SENSOR_IP: Final = "IP"
SENSOR_VERSION: Final = "Version"
SENSOR_BUILD: Final = "Build"
SENSOR_WIFI: Final = "Wifi"
SENSOR_DISK: Final = "disk"
SENSOR_MEM: Final = "mem"
SENSOR_PROC: Final = "proc"
SENSOR_PROC_NUMB: Final = "proc_numb"

# Binary sensor keys
BINARY_SENSOR_PRINTING: Final = "Printing"
BINARY_SENSOR_PAUSED: Final = "Paused"
BINARY_SENSOR_HALTED: Final = "Halted"
BINARY_SENSOR_PANICKED: Final = "Panicked"
BINARY_SENSOR_FORCE_STOP: Final = "ForceStop"
BINARY_SENSOR_AUTO_SHUTDOWN: Final = "AutoShutdown"
BINARY_SENSOR_COVERED: Final = "Covered"
BINARY_SENSOR_CAST: Final = "Cast"
BINARY_SENSOR_CAMERA: Final = "Camera"

# Other fields
FIELD_REAL_TIME_EST: Final = "RealTimeEst"
FIELD_RESUME_ID: Final = "ResumeID"
FIELD_SLICING_PLATE_ID: Final = "SlicingPlateID"
FIELD_START_AFTER_SLICE: Final = "StartAfterSlice"
FIELD_PANIC_ROW: Final = "PanicRow"
FIELD_PLATE_ID: Final = "PlateID"
FIELD_LOG: Final = "log"
FIELD_PLAY: Final = "play"

# Device info
MANUFACTURER: Final = "Concepts3D"
MODEL: Final = "Athena II"
