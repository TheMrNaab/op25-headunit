# Linux System Utilities for OP25

The `linuxSystem` directory contains system-level utility modules that support audio, display, power, and networking features in the OP25 headunit environment. These modules are used internally by the API and background processes to retrieve and manage system status in real-time.

---

## linuxUtils.py

The `LinuxUtilities` class provides a collection of static utility methods for interacting with a Linux system.

### Audio-Related Methods

- **`get_active_audio_device_old()`**  
  Fetches properties of active PipeWire audio sinks using a shell command and parses the JSON output.

- **`get_audio_sink_properties()`**  
  Retrieves detailed audio sink properties and handles systems with multiple active results.

- **`get_volume_percent()`**  
  Reads the system's current volume level using the `amixer` command.

### QR Code Generation

- **`generate_qrcode_image(content)`**  
  Creates a QR code for the provided content and returns it as a `BytesIO` image stream.

### Display Management

- **`set_display_timeout(display_id, timeout)`**  
  Sets the DPMS (Display Power Management Signaling) timeout for a given display.

- **`get_display_timeout(display_id)`**  
  Gets the current DPMS timeout value.

- **`list_displays()`**  
  Lists all active and inactive displays, including their IDs, names, and usage states.

### Device Sleep Management

- **`set_device_sleep_timeout(timeout_seconds)`**  
  Configures the system idle delay before going to sleep.

- **`get_device_sleep_timeout()`**  
  Returns the current idle timeout value.

### Network and System Information

- **`get_local_ip()`**  
  Retrieves the IP address of the active network interface.

- **`get_network_status()`**  
  Compiles and returns a full snapshot of network type, WiFi status, memory availability, CPU temperature, and active audio output.

### System Monitoring

- Uses `psutil` to pull system statistics.
- Reads thermal status from the system's temperature zone files.

---

## sound.py

The `soundSys` class provides utility methods for managing and interacting with audio hardware on Linux systems.

### Volume Management

- **`get_volume_percent()`**  
  Uses `amixer` to retrieve current volume as a percentage.

- **`set_volume(level)`**  
  Sets the system volume to the specified percentage using `amixer`.

- **`parse_volume(output)`**  
  Parses `amixer` command output to extract structured volume data including:
  - Capabilities
  - Playback channels
  - Volume limits

### Audio Device Parsing

- **`parse_hw_devices()`**  
  Scans connected audio hardware using `aplay -l` and filters them through `aplay -L` to build a usable device map.

- **`list_alsa_devices()`**  
  Lists all ALSA-supported devices using `aplay -L`.

### Error Handling

- Includes error checking and exception handling for subprocess calls, with detailed debug output when command execution fails.

---

These tools are integrated into the broader OP25 project and assist with providing real-time feedback to the user interface. No direct configuration is required by end users.
