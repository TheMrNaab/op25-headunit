# OP25 Headunit API Reference

The `api.py` file in the `op25-headunit` repository serves as the central API backend. It is built using Flask and exposes a structured set of RESTful API endpoints for controlling, monitoring, and configuring the OP25 scanner system.

---

## Overview

### Core Features
- Flask app initialization with CORS support
- Session and system state management
- Real-time log and event streaming
- Frontend/backend integration with hardware-level control

---

## API Endpoint Reference

### System Control
- **[GET]** `/volume/simple` — Get system volume level (0–100)
- **[PUT]** `/volume/<int:level>` — Set system volume level
- **[GET]** `/device/audio/properties` — Get active sound device properties
- **[GET]** `/device/audio/properties/<property>` — Get a specific audio property

### System Utilities
- **[GET]** `/utilities/qrcode/<path:content>` — Generate a QR code for the given content

### Display Sleep Settings
- **[PUT]** `/config/openbox/display/<int:id>/sleep/set/<int:timeout>` — Set display sleep timeout
- **[GET]** `/config/openbox/display/<int:id>/sleep` — Get display sleep timeout

### Device Sleep Settings
- **[POST]** `/config/openbox/device/sleep/set/<int:timeout>` — Set device sleep timeout
- **[GET]** `/config/openbox/device/sleep` — Get device sleep timeout

### Display Listing
- **[GET]** `/config/openbox/device/displays` — List all displays

### Network
- **[GET]** `/config/network` — Get network status

### Zone and Channel Data
- **[GET]** `/zone/<int:zone_number>/channel/<int:channel_number>` — Get channel data
- **[GET]** `/zone/<int:zone_number>/channel/<int:channel_number>/next` — Get next channel
- **[GET]** `/zone/<int:zone_number>/channel/<int:channel_number>/previous` — Get previous channel

### Active Session State
- **[GET]** `/session/channel/field/<field_name>` — Get a field from the active channel
- **[GET]** `/session/channel` — Get full active channel object
- **[PUT]** `/session/channel/go/<int:channel_number>` — Go to a specific channel
- **[GET]** `/session/zone` — Get full active zone object
- **[GET]** `/session/talkgroups/<tgid>/name/plaintext` — Get talkgroup name
- **[GET]** `/session/talkgroups` — Get all active talkgroups

### Session Modifiers
- **[PUT]** `/session/channel/<int:id>` — Set active channel by ID
- **[PUT]** `/session/zone/<int:zn>/channel/<int:ch>` — Set zone and channel
- **[PUT]** `/session/channel/next` — Go to next channel
- **[PUT]** `/session/channel/previous` — Go to previous channel
- **[PUT]** `/session/zone/<int:id>` — Set zone by ID
- **[PUT]** `/session/zone/next` — Go to next zone
- **[PUT]** `/session/zone/previous` — Go to previous zone

### Zone Data
- **[GET]** `/zones` — Get all zones
- **[GET]** `/zone/<int:zone_number>` — Get a zone by index
- **[GET]** `/zone/<int:zone_number>/previous` — Get previous zone
- **[GET]** `/zone/<int:zone_number>/next` — Get next zone

### OP25 Radio Controls
- **[POST]** `/session/controller/whitelist` — Whitelist TGIDs
- **[PUT]** `/session/controller/lockout/<int:tgid>` — Lock out a TGID
- **[PUT]** `/session/controller/hold/<int:tgid>` — Hold a TGID
- **[PUT]** `/controller/restart` — Restart OP25

### Streaming and Logging
- **[POST]** `/controller/logging/update` — Push log data to clients
- **[GET]** `/controller/logging/stream` — Stream logs (SSE)
- **[GET]** `/controller/progress` — Stream TGID update progress
- **[POST]** `/controller/progress/update/<int:percent>` — Set progress value

### Admin Portal
- **[GET]** `/admin/systems/` — Get systems file
- **[POST]** `/admin/systems/update` — Update systems file
- **[GET]** `/admin/talkgroups/all` — Get all TGIDs
- **[POST]** `/admin/zones/update` — Update zones file
- **[GET]** `/admin/config/get` — Get config file
- **[POST]** `/admin/config/set` — Update config file
- **[GET]** `/admin/config/device/<property>` — Get device property

### Configuration
- **[GET]** `/config/op25/get` — Get OP25 config
- **[POST]** `/config/op25/post` — Update OP25 config
- **[GET]** `/config/reload` — Reload config
- **[POST]** `/config/talkgroups/post` — Update talkgroups file
- **[GET]** `/config/audio-devices` — List audio devices

---

This file provides the foundational interface for external control and integration with the OP25 scanner system.
