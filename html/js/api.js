// api.js
export const print_debug = true; // Toggle debug output

// Set base API URL dynamically based on the current hostname
export const API_BASE_URL = `http://${location.hostname}:5001`;

// API endpoints organized into logical groups
export const APIEndpoints = Object.freeze({
    SYSTEMS: {
        // These endpoints do not exist in your current API, keep only if you plan to add them
    },

    LOGGING: {
        UPDATE: "/controller/logging/update",
        STREAM: "/controller/logging/stream"
    },

    ZONES: {
        LIST: "/zones",
        GET_ONE: (index) => `/zone/${index}`,
        CHANNEL_ONE: (zone, ch) => `/zone/${zone}/channel/${ch}`,
        CHANNEL_NEXT: (zone, ch) => `/zone/${zone}/channel/${ch}/next`,
        CHANNEL_PREVIOUS: (zone, ch) => `/zone/${zone}/channel/${ch}/previous`,
        ZONE_NEXT: (zone) => `/zone/${zone}/next`,
        ZONE_PREVIOUS: (zone) => `/zone/${zone}/previous`
    },

    SESSION: {
        CHANNEL_CURRENT: "/session/channel",
        ZONE_CURRENT: "/session/zone",
        TALKGROUP_NAME: (tgid) => `/session/talkgroups/${tgid}/name/plaintext`,
        TALKGROUP_LIST: "/session/talkgroups",
        CHANNEL_FIELD: (field) => `/session/channel/field/${field}`,
        CHANNEL_SELECT: (id) => `/session/channel/${id}`,
        CHANNEL_NEXT: "/session/channel/next",
        CHANNEL_PREVIOUS: "/session/channel/previous",
        ZONE_SELECT: (id) => `/session/zone/${id}`,
        ZONE_NEXT: "/session/zone/next",
        ZONE_PREVIOUS: "/session/zone/previous"
    },

    VOLUME: {
        GET_SIMPLE: "/volume/simple",
        SET: (level) => `/volume/${level}`
    },

    PROGRESS: {
        STREAM: "/controller/progress",
        UPDATE: (percent) => `/controller/progress/update/${percent}`
    },

    UTILITIES: {
        QR_CODE: (content) => `/utilities/qrcode/${encodeURIComponent(content)}`
    },

    CONFIG: {
        NETWORK: "/config/network",
        SET: (section, property, value) => `/config/set/${section}/${property}/${value}`,
        GET_JSON: "/config/get/json",
        SET_JSON: "/config/set/json"
    },

    DISPLAY: {
        SET_SLEEP: (id, timeout) => `/config/openbox/display/${id}/sleep/set/${timeout}`,
        GET_SLEEP: (id) => `/config/openbox/display/${id}/sleep`
    },

    DEVICE: {
        SET_SLEEP: (timeout) => `/config/openbox/device/sleep/set/${timeout}`,
        GET_SLEEP: "/config/openbox/device/sleep",
        GET_AUDIO_PROPERTY: (property) => `/device/audio/properties/${property}`,
        GET_AUDIO_PROPERTIES: "/device/audio/properties"
    },

    NETWORK: "/config/network",

    CONTROLLER: {
        WHITELIST: "/session/controller/whitelist",
        LOCKOUT: (tgid) => `/session/controller/lockout/${tgid}`,
        HOLD: (tgid) => `/session/controller/hold/${tgid}`,
        RESTART: "/controller/restart"
    }
});

export async function apiGet(url) {
    var url = `${API_BASE_URL}${url}`;
    console.log(url);
    const res = await fetch(`${url}`, {
      method: "GET",
      credentials: "include"
    });
    if (!res.ok) throw new Error(`API error: ${await res.text()}`);
    return res.json();
  }

export async function apiGetV2(url) {
    var url = `${API_BASE_URL}${url}`;
    console.log(url);
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response; // This should be a Response object
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