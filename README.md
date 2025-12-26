# Concepts3D Athena II Home Assistant Integration

<!--
Uncomment and add your logo image to .github/ directory:
<p align="center">
  <img src=".github/logo.png" alt="Athena II Logo" width="400"/>
</p>
-->

A custom Home Assistant integration for the Concepts3D Athena II resin 3D printer.

## Features

- **Real-time Monitoring**: Poll printer status every 30 seconds (configurable)
- **Comprehensive Sensors**: All printer status fields exposed as Home Assistant sensors
- **Binary Sensors**: Quick status indicators for printing, paused, halted, and error states
- **Camera Support**: Live camera feed with automatic 90° clockwise rotation
- **Easy Configuration**: UI-based configuration flow
- **HACS Compatible**: Install directly through HACS

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL and select "Integration" as the category
6. Click "Install"
7. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/athena2` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "+ Add Integration"
3. Search for "Concepts3D Athena II"
4. Enter your printer's IP address (e.g., `192.168.0.49`)
5. Optionally configure the port (default: 80) and scan interval (default: 30 seconds)
6. Click Submit

## Available Entities

### Sensors

**Print Status & Progress**
- Status - Current printer status message
- Current Layer - Current layer being printed
- Total Layers - Total layers in the print job
- Print Progress - Percentage of print completed
- Estimated Time Remaining - Estimated time to completion

**Positioning**
- Current Height - Current Z-axis position (mm)
- Plate Height - Build plate height (mm)

**Timing**
- Layer Time - Time for current layer (seconds)
- Previous Layer Time - Time for previous layer (seconds)

**Temperatures**
- System Temperature - Overall system temperature (°C)
- MCU Temperature - Microcontroller temperature (°C)
- Resin Temperature - Resin vat temperature (°C)
- Vat Temperature - Resin vat temperature (analytic) (°C)
- Vat Temperature Target - Target vat temperature (°C)
- Chamber Temperature - Print chamber temperature (°C)
- Chamber Temperature Target - Target chamber temperature (°C)
- Inside Temperature - Inside enclosure temperature (°C)
- Inside Temperature Target - Target inside temperature (°C)
- Outside Temperature - Outside ambient temperature (°C)
- Outside Temperature Target - Target outside temperature (°C)
- PTC Temperature - PTC heater temperature (°C)
- PTC Temperature Target - Target PTC temperature (°C)

**Fans**
- MCU Fan Speed - MCU cooling fan speed (RPM)
- UV Fan Speed - UV light cooling fan speed (RPM)
- PTC Fan Speed - PTC fan speed (RPM)
- AEGIS Fan Speed - AEGIS fan speed (RPM)

**Materials**
- Resin Level - Current resin level (mm)
- Lamp Hours - UV lamp usage hours

**System Resources**
- Disk Usage - Storage usage (%)
- Memory Usage - RAM usage (%)
- CPU Usage - Processor usage (%)
- Process Count - Number of running processes

**System Information**
- Uptime - System uptime
- Hostname - Printer hostname
- IP Address - Printer IP address
- Firmware Version - Firmware version number
- WiFi - WiFi network name

**Environmental**
- VOC Inlet Air Quality - Air quality at inlet (0-100%, higher is better)
- VOC Outlet Air Quality - Air quality at outlet (0-100%, higher is better)
- Pressure - Chamber pressure

**Print Parameters (Analytic)**
- Lift Height - Z-axis lift height (mm)
- Cure Time - Layer cure time (seconds)
- Dynamic Wait - Dynamic wait time (seconds)
- Speed - Print speed
- Solid Area - Solid cross-sectional area
- Area Count - Number of separate areas
- Largest Area - Size of largest area

### Binary Sensors

- **Printing** - Is the printer actively printing?
- **Paused** - Is the print paused?
- **Halted** - Is the printer halted?
- **Panicked** - Is the printer in a panic/error state?
- **Force Stop** - Has a force stop been triggered?
- **Auto Shutdown** - Is auto shutdown enabled?
- **Covered** - Is the printer cover closed?
- **Cast** - Is casting enabled?

### Camera

- **Camera** - Live camera feed with automatic 90° clockwise rotation

## Services

The integration provides the following services to control your printer:

### Print Control Services

- **`athena2.pause_print`** - Pause the current print job
  - Only works when a print is actively running
  - Target: Any Athena II sensor entity

- **`athena2.resume_print`** - Resume a paused print job
  - Only works when a print is paused
  - Target: Any Athena II sensor entity

- **`athena2.cancel_print`** - Cancel the current print job
  - The printer will complete the current layer before stopping (safe stop)
  - Target: Any Athena II sensor entity

- **`athena2.set_auto_shutdown`** - Enable or disable automatic shutdown after print completion
  - Parameters:
    - `enabled` (boolean, required): True to enable, False to disable
  - Target: Any Athena II sensor entity

- **`athena2.start_print`** - Start a print job by plate ID
  - **WARNING**: Ensure the printer is ready (resin filled, plate installed) before starting
  - Parameters:
    - `plate_id` (text, required): The ID of the plate/job to print
  - Target: Any Athena II sensor entity
  - Note: To find available plate IDs, check your printer's web interface at `http://[PRINTER_IP]/plates`

### System Control Services

- **`athena2.shutdown`** - Shut down the entire printer system
  - **WARNING**: This will power off the printer completely
  - Use with caution
  - Target: Any Athena II sensor entity

- **`athena2.reboot`** - Reboot the entire printer system
  - **WARNING**: This will restart the printer completely
  - Use with caution
  - Target: Any Athena II sensor entity

### Using Services

Services can be called from:
1. **Developer Tools → Services** in Home Assistant
2. **Automations** - trigger printer actions based on conditions
3. **Scripts** - create reusable printer control sequences
4. **Dashboards** - add buttons to control printer from UI

Example automation:
```yaml
automation:
  - alias: "Pause print if door opens"
    trigger:
      - platform: state
        entity_id: binary_sensor.athena_ii_192_168_0_49_covered
        to: "off"  # Door opened
    condition:
      - condition: state
        entity_id: binary_sensor.athena_ii_192_168_0_49_printing
        state: "on"
    action:
      - service: athena2.pause_print
        target:
          entity_id: sensor.athena_ii_192_168_0_49_status
```

## Configuration Options

After initial setup, you can modify these options:

- **Scan Interval**: How often to poll the printer (10-300 seconds)
- **Camera Frame Rate**: How often to fetch and rotate camera frames (0.1-5 FPS)
  - **0.1 FPS** = 1 frame every 10 seconds (default)
  - **1 FPS** = 1 frame per second (smooth)
  - **5 FPS** = 5 frames per second (near real-time, higher CPU usage)

To change options:
1. Go to Settings → Devices & Services
2. Find your Athena II printer
3. Click "Configure"

**Note**: Higher camera frame rates will use more CPU due to rotating each frame. Start with 1 FPS for smooth viewing, increase to 5 FPS for near-live monitoring.

## Troubleshooting

### Printer Not Found

- Verify the printer is powered on and connected to your network
- Check that the IP address is correct
- Ensure your Home Assistant instance can reach the printer (same network/VLAN)
- Try accessing `http://[PRINTER_IP]/status` in a web browser

### Camera Not Working

- Verify the camera stream is accessible at `http://[PRINTER_IP]/athena-camera/stream`
- Check Home Assistant logs for camera-related errors
- The camera requires the Pillow library for image rotation

### Sensors Showing "Unavailable"

- Check that the printer is responding to status requests
- Verify network connectivity
- Look in Home Assistant logs for error messages
- Try reloading the integration

### High CPU Usage

- The camera rotation feature processes images in real-time, which may impact performance on slower systems
- Consider increasing the scan interval to reduce polling frequency

## API Endpoints

This integration uses the following Athena II API endpoints:

- **Status**: `http://[IP]/status` - Returns JSON with all printer data
- **Camera**: `http://[IP]/athena-camera/stream` - MJPEG camera stream

## Development

### Discovering Control API Endpoints

To implement printer control services, you'll need to discover the API endpoints:

1. Open your printer's web interface in a browser
2. Open browser Developer Tools (F12)
3. Go to the Network tab
4. Perform actions like pause, resume, cancel
5. Look for API calls in the network log
6. Document the endpoints and update the integration

### Contributing

Contributions are welcome! Please:

1. Fork this repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Credits

- Integration developed for the Concepts3D Athena II resin printer
- API information derived from the [Orion project](https://github.com/Open-Resin-Alliance/Orion)

## Historical Sensor Data

Home Assistant automatically records sensor history using the built-in [Recorder](https://www.home-assistant.io/integrations/recorder/) integration. All Athena II sensor data is tracked by default.

### Viewing Historical Data

1. **History Panel** - Click on any sensor to view its history graph
2. **Logbook** - View all state changes over time
3. **Energy Dashboard** - Track long-term trends (for supported sensors)
4. **Custom Cards** - Use history graphs in Lovelace dashboards

### Long-term Statistics

The following sensors provide long-term statistics that are kept indefinitely:
- Lamp Hours
- Total Layers (calculated from prints)
- Print Progress tracking
- System uptime
- All temperature sensors

### Database Retention

By default, Home Assistant keeps 10 days of detailed history. To extend this:

```yaml
# configuration.yaml
recorder:
  purge_keep_days: 30  # Keep 30 days of history
  db_url: "postgresql://user:password@localhost/homeassistant"  # For better performance
```

## Future Features (Planned)

The following features are planned for future releases:

### Camera LED Control
- Switch to control camera LED on/off
- Requires discovery of G-code execution endpoint

### Print History from Database
- Sensors showing last print details
- Total print count
- Print success/failure statistics
- Access to SQLite database `/home/pi/printer/db/tracking.db`

These features require additional investigation and will be added in future updates.

## Support

For issues, questions, or feature requests, please open an issue on GitHub.
