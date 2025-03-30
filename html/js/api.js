// api.js
export const print_debug = true; // Toggle debug output

// Set base API URL dynamically based on the current hostname
export const API_BASE_URL = `http://${location.hostname}:5001`;

// API endpoints organized into logical groups
export const APIEndpoints = Object.freeze({
    SYSTEMS: {
        LIST: "/v2/systems/list",
        GET_ONE: (id) => `/v2/systems/${id}`,
        NEW: "/v2/systems/new",
        TGID_ALL: (id) => `/v2/systems/${id}/tgid/`,
        TGID_ONE: (id, tgid) => `/v2/systems/${id}/tgid/${tgid}`
    },

    LOGGING: {
        UPDATE: "/logging/update",
        STREAM: "/logging/stream"
    },

    ZONES: {
        LIST: "/v2/zones",
        GET_ONE: (index) => `/v2/zones/${index}`,
        CHANNELS_ALL: (index) => `/v2/zones/${index}/channels`,
        CHANNEL_ONE: (index, ch) => `/v2/zones/${index}/channel/${ch}`,
        NEW: "/v2/zones/new",
        CHANNELS_NEW: (index) => `/v2/zones/${index}/channels/new`,
        CHANNEL_NEW: (index) => `/v2/zones/${index}/channel/new`
    },

    SESSION: {
        START: "/v2/session/start",
        STATUS: "/v2/session/status",
        SYSTEM_CURRENT: "/v2/session/system/current",
        CHANNEL_CURRENT: "/v2/session/channel/current",
        CHANNEL_NEXT: "/v2/session/channel/next",
        CHANNEL_PREVIOUS: "/v2/session/channel/previous",
        ZONE_NEXT: "/v2/session/zone/next",
        ZONE_PREVIOUS: "/v2/session/zone/previous",
        ZONE_CURRENT: "/v2/session/zone/current",
        CHANNEL_SELECT: (channelNumber) => `/v2/session/channel/${channelNumber}`,
        ZONE_SELECT: (id) => `/v2/session/zone/${id}`
    },

    VOLUME: {
        GET_SIMPLE: "/volume/simple",
        SET: (level) => `/volume/${level}`
    },

    PROGRESS: {
        STREAM: "/progress",
        UPDATE: (percent) => `/update/${percent}`
    },

    UTILITIES: {
        QR_CODE: (content) => `/utilities/qrcode/${encodeURIComponent(content)}`
    },

    DISPLAY: {
        SET_SLEEP: (id, timeout) => `/config/openbox/display/${id}/sleep/set/${timeout}`,
        GET_SLEEP: (id) => `/config/openbox/display/${id}/sleep/`,
        LIST: "/config/openbox/device/displays"
    },

    DEVICE: {
        SET_SLEEP: (timeout) => `/config/openbox/device/sleep/set/${timeout}`,
        GET_SLEEP: "/config/openbox/device/sleep/"
    },

    CONFIG: {
        HOSTS: "/config/host",
        SET: (section, property, value) => `/config/set/${section}/${property}/${value}`,
        GET_JSON: "/config/get/json",
        SET_JSON: "/config/set/json"
    },

    NETWORK: "/config/network",

    SYSTEM_CONFIG: {
        GET: "/config/system/",
        UPDATE: "/config/system/update"
    },

    CHANNEL_CONFIG: {
        GET: "/config/channels/",
        UPDATE: "/config/channels/update"
    },

    TALKGROUP_CONFIG: {
        GET: "/config/talkgroups/",
        UPDATE: "/config/talkgroups/update"
    },

    RESTART: "/restart"
});

export async function apiGet(url) {
    const res = await fetch(`${API_BASE_URL}${url}`, {
      method: "GET",
      credentials: "include"
    });
    if (!res.ok) throw new Error(`API error: ${await res.text()}`);
    return res.json();
  }
  
  export async function apiPut(url, body = null) {
    const res = await fetch(`${API_BASE_URL}${url}`, {
      method: "PUT",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : null
    });
    if (!res.ok) throw new Error(`API error: ${await res.text()}`);
    return res.json();
  }