# OP25 Admin Interface

This directory (`/admin`) contains the configuration management interface for the OP25 headunit. It allows administrators to create, edit, and organize the systems, zones, channels, and talkgroups used by the scanner.

## Overview

Each HTML file in this directory provides a focused interface for editing specific elements of the OP25 configuration. These interfaces send and receive data via API calls handled by the `api.py` backend.

## File Descriptions

- **index.html**  
  Dashboard view or entry point into the admin tools.

- **channels.html**  
  Interface for managing channels within zones. Allows editing of channel names, frequencies, and assignments.

- **op25.html**  
  Allows customization of settings related to the Op25 launch arguments. The device (e.g. Raspberry Pi) must be restarted for these changes to take effect. 

- **system.html**  
  Used to define and manage OP25 trunking systems, including NAC, modulation, and control channel parameters.

- **talkgroups.html**  
  Interface for assigning and labeling talkgroup IDs (TGIDs) across systems for easier recognition and priority handling.

- **backend.css**  
  Stylesheet used across the admin pages for consistent layout and design.

## Purpose

The admin panel provides a structured way to update scanner behavior without editing JSON or TSV files manually. Changes made in the admin interface are processed by the API and written directly to backend configuration files.

