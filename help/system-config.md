# Configuring `system.json` for OP25

## Overview
The `system.json` file is a critical configuration file for OP25, defining the channels, zones, and talkgroups the system will monitor. This file must be stored in the root directory of the script installation at:
```
/opt/op25-project/system2.json
```

### Getting Started
To configure OP25 properly, ensure you have the correct talkgroup IDs and channel information. **Radio Reference** (radioreference.com) is a recommended source for obtaining this information.

### Creating & Editing `system.json`
Utilize the System Configurator in `/html/utilities/system-editor`

### Copy Downloaded File
Copy the downloaded file to `/opt/op25-project/system2.json`

## Other Requirements
Install other packages that are needed
```sudo apt install nodejs npm```