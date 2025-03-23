// Define the new host with a different constant name

const API_BASE_URL = "http://192.168.1.44:5001"; // Replace with your actual API base URL

// Reusable GET request helper with error handling
async function apiGet(endpoint) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    if (!response.ok) {
        const error = await response.text();
        throw new Error(`API error: ${error}`);
    }
    return await response.json();
}

// Get zone of a specific channel
async function fetchChannelZone(channelNumber) {
    return await apiGet(`/channel/${channelNumber}/zone`);
}

async function fetchNextChannel(zoneNumber, channelNumber) {
    return await apiGet(`/zone/${zoneNumber}/channel/${channelNumber}/next`);
}

async function fetchPreviousChannel(zoneNumber, channelNumber) {
    return await apiGet(`/zone/${zoneNumber}/channel/${channelNumber}/previous`);
}

// Get all zones
async function fetchAllZones() {
    return await apiGet("/zones");
}

// FETCH ZONE
async function fetchZone(zoneNumber) {
    return await apiGet(`/zone/${zoneNumber}/next`);
}

// Get next zone relative to the current one
async function fetchNextZone(zoneNumber) {
    return await apiGet(`/zone/${zoneNumber}/next`);
}

// Get previous zone relative to the current one
async function fetchPreviousZone(zoneNumber) {
    return await apiGet(`/zone/${zoneNumber}/previous`);
}

async function fetchChannel(zoneNumber, channelNumber) {
    return await apiGet(`/zone/${zoneNumber}/channel/${channelNumber}`);
}

async function switchTalkGroups(channelData) {
    console.log("channelData:", channelData);
    try {
        let tgids;
        if (Array.isArray(channelData)) {
            tgids = channelData;
        } else if (Array.isArray(channelData.tgid)) {
            tgids = channelData.tgid;
        } else {
            throw new Error("No TGIDs provided in channelData");
        }

        const response = await fetch(`${API_BASE_URL}/whitelist`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ tgid: tgids })
        });

        if (!response.ok) {
            const error = await response.text();
            throw new Error(`Whitelist API error: ${error}`);
        }

        const result = await response.json();
        // console.log("Whitelist success:", result);
        return result;
    } catch (err) {
        console.error("Failed to send whitelist:", err.message);
    }
}


// Example usage (wrap in try/catch if calling from UI event handlers)
async function testCalls() {
    try {
        const zone = await fetchZone(0);
        console.log("Zone 0:", zone);

        const nextZone = await fetchNextZone(0);
        console.log("Next Zone:", nextZone);

        const channelZone = await fetchChannelZone(47);
        console.log("Zone for Channel 47:", channelZone);

        const nextChannel = await fetchNextChannel(47);
        console.log("Next Channel after 47:", nextChannel);

        const prevChannel = await fetchPreviousChannel(47);
        console.log("Previous Channel before 47:", prevChannel);
    } catch (err) {
        console.error("API error:", err.message);
    }
}



