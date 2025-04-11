# OP25 Head Unit Web Interface

This directory contains the full HTML frontend for the OP25 head unit, designed to be served locally via the Flask-based `api.py` backend at `http://localhost:8000`.

## Overview

The `index.html` file serves as the main graphical user interface for controlling an OP25 software-defined radio scanner. The interface is optimized for touchscreen use in vehicles or desktop environments.

## Directory Contents

- **index.html**  
  The main UI for the OP25 head unit. Allows users to view zones, talkgroups, change channels, adjust volume, and use a keypad for direct entry.

- **/static/**  
  Contains all front-end assets, organized as follows:
  - **/css** — Stylesheets for front-end customization
  - **/bootstrap** — Bootstrap framework files
  - **/fa** — Font Awesome icon library
  - **/webfonts** — Font Awesome font files
  - **/js** — Supporting JavaScript code for front-end functionality
  - **/audio** Contains audio files for the numeric keypad and bottom function buttons. 

- **/admin/**  
  Contains configuration tools and interfaces for:
  - System setup
  - Zone management
  - Channel definition
  - Talkgroup tagging

  This back-end admin panel allows real-time updates to configuration files via the API.

## API Integration

All interaction between the frontend and the OP25 backend is handled through `api.py`, which serves:
- The static frontend at `http://localhost:8000`
- RESTful API endpoints for volume control, system switching, talkgroup lookup, and configuration updates

## How to Use

1. Ensure the `api.py` backend is running.
2. Visit `http://localhost:8000` in your browser or on your touchscreen device.
3. Use the interface to:
   - Select zones and channels
   - Adjust volume
   - Access keypad for direct TGID entry
   - Open modals to manage zone or channel lists
4. Visit `http://localhost:8000/admin` to access the system configuration portal.

## Notes

- All configuration changes are persisted through backend file updates.
- Ensure CORS is properly configured in `api.py` to allow full frontend interaction.
- Interface is mobile-friendly and designed for low-latency feedback.
