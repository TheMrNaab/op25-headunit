# Configuring `system.json` for OP25

## Overview
The `system.json` file is a critical configuration file for OP25, defining the channels, zones, and talkgroups the system will monitor. This file must be stored in the root directory of the script installation at:
```
/opt/op25-project/system.json
```

### Getting Started
To configure OP25 properly, ensure you have the correct talkgroup IDs and channel information. **Radio Reference** (radioreference.com) is a recommended source for obtaining this information.

### JSON File Structure
Each entry in the `system.json` file represents a different channel or talkgroup. Below is an example:

```json
[
    {
        "channel_number": 1,
        "name": "Fire Scan",
        "zone": "Fire",
        "type": "Scan",
        "tgid": [
            46949, 47021, 46940, 46800, 46801
        ]
    },
    {
        "channel_number": 2,
        "name": "ALERT SCAN",
        "zone": "Fire",
        "type": "Scan",
        "tgid": [46949, 47021]
    },
    {
        "channel_number": 3,
        "name": "WC FD ALERT",
        "zone": "Fire",
        "type": "talkgroup",
        "tgid": [46949]
    }
]
```

### Breakdown of Fields
- **`channel_number`** – Unique number assigned to the channel.
- **`name`** – Friendly name for the channel.
- **`zone`** – The category the channel belongs to (e.g., Fire, Law, EMS).
- **`type`** – Defines whether this is a "Scan" (listening to multiple talkgroups) or "talkgroup" (monitoring a single TGID).
- **`tgid`** – A list of talkgroup IDs (TGIDs) to monitor for the channel.

### Creating & Editing `system.json`
1. **Use a JSON Editor** – A good JSON editor (such as [jsonlint.com](https://jsonlint.com) for validation) can help avoid syntax errors.
2. **Follow Proper Formatting** – Ensure all brackets, commas, and quotation marks are correctly placed.
3. **Validate the JSON** – Before saving, validate your JSON using an online validator or a command-line tool:
   ```bash
   jq . system.json
   ```
4. **Save & Restart OP25** – Once configured, save the file and restart OP25 for the changes to take effect.

## Final Notes
- Ensure **no trailing commas** are left in the JSON file.
- Use **consistent indentation** for readability.
- Use **unique channel numbers** to avoid conflicts.

After setup, OP25 will automatically load the channels and talkgroups defined in `system.json` and begin monitoring as configured.