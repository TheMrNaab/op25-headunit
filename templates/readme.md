# OP25 Templates Directory

This directory (`/templates`) contains supplemental files used by the OP25 headunit for internal processing and frontend event integration. Most files are handled automatically and do not require user modification.

## File Descriptions

- **_blist.tsv**  
  Reserved file for storing blacklist entries. Used internally for reference only. Users do not need to configure or modify this file.

- **_tgroups.csv**  
  Stores exported talkgroup data for internal system use. This is a generated file and does not require user input.

- **_trunk.tsv**  
  Contains trunking system data for reference. Automatically populated and does not require user setup.

- **_whitelist.tsv**  
  Similar to `_blist.tsv`, this file is used for managing whitelisted talkgroups. Stored for backend reference.

- **trunking.py**  
  A modified version of the core OP25 trunking handler. This script must be **manually copied into the user's OP25 installation folder**. It is responsible for emitting real-time trunking events to the frontend interface, enabling:
  - Display of current and active talkgroups
  - Lock and hold actions
  - Event status such as active/inactive

  Instructions for copying and using this modified file are included in the main repository `README.md`.

## Notes

- Do not manually edit or delete the `.tsv` and `.csv` files.
- These files are used to track internal scanner state and configurations.
- Only `trunking.py` requires user action and is essential for enabling real-time communication between OP25 and the frontend.

