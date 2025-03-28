

// Global Variables
// API URL for the new API is in api.js

const config = {
  channelEntryTimer: null,
  print_debug: true,
  allZones: [],
  activeChannelNumber: null,
  activeChannelIndex: -1,
  activeChannel: [],
  activeZoneData: [],   // Store the full zone object
  activeZoneName: null,
  activeZoneIndex: -1,
  whitelist: []
};

init();

function init() {
  document.addEventListener("DOMContentLoaded", async () => {

  //AKNOWLEDGE LOADING
  console.log("DOM fully loaded and parsed");

  // VOLUME ADJUSTMENT LISTENER
  document.getElementById("volumeRange").addEventListener("change", function () {
    const level = this.value;
    sendVolume(level);
  });

  // SET CURRENT VOLUME AND UPDATE THE INITIAL SLIDER COLOR
  fetchCurrentVolume();


  // SET THE EVENT LISTENER FOR UPDATING SLIDER COLOR BASED ON VALUE
  slider.addEventListener("input", () => {
      updateSliderColor(slider.value);
  });


  try {
    const data = await fetchAllZones();
    const zones = data.zones || [];
    config.allZones = zones;
    config.activeZoneData = zones[0];
    config.activeZoneIndex = 0;
    config.activeZoneName = zones[0].name;
    updateConfig2(config.allZones[0].channels[0]);

  } catch (err) {
    console.error("Failed to load zones:", err);
    showAlert("Failed to load zones.");
  }

  // Button listeners
  const btnZoneList = document.getElementById("btnZoneList");
  if (btnZoneList) {
    btnZoneList.addEventListener("click", openZoneModal);
  }

    const btnChannelList = document.getElementById("btnChannelList");
    if (btnChannelList) {
      btnChannelList.addEventListener("click", _channelList);
    }

    const btnZoneUp = document.getElementById("btnZoneUp");
    if (btnZoneUp) {
      btnZoneUp.addEventListener("click", _btnZoneUp);
    }

    const btnZoneDown = document.getElementById("btnZoneDown"); // fixed ID typo
    if (btnZoneDown) {
      btnZoneDown.addEventListener("click", _btnZoneDown);
    }

    const btnChannelUp = document.getElementById("btnChannelUp");
    if (btnChannelUp) {
      btnChannelUp.addEventListener("click", _btnChannelUp);
    }

    const btnChannelDown = document.getElementById("btnChannelDown");
    if (btnChannelDown) {
      btnChannelDown.addEventListener("click", _btnChannelDown);
    }

    const zoneApplyBtn = document.getElementById("zone-apply");
    if (zoneApplyBtn) {
      zoneApplyBtn.addEventListener("click", _zoneApplyBtn);
    }

    const channelApplyBtn = document.getElementById("channel-apply");
    if (channelApplyBtn) {
      channelApplyBtn.addEventListener("click", _channelApplyBtn);
    }

    function _channelApplyBtn() {
      const selectElement = document.getElementById('channels'); // Ensure selectElement is defined
      const channels = config.activeZoneData.channels; // Ensure channels is defined
    
      const selectedChannelNumber = parseInt(selectElement.value);
      const selectedChannel = channels.find(ch => ch.channel_number === selectedChannelNumber);
      if (!selectedChannel) {
        console.error("Channel not found in zone:", selectedChannelNumber);
        return;
      }
      try {
        updateConfig2(selectedChannel);
        updateUI();
        channelModal.hide();
        switchTalkGroups(config.activeChannel.tgid).catch(error => {
          console.error("Error setting channel:", error);
          alert("Error setting channel: " + error.message);
        });
      } catch (error) {
        console.error("Error setting channel:", error);
        alert("Error setting channel: " + error.message);
      }
    }

    // Control mappings for select elements
    const controls = [
      {
        list: document.getElementById("zones"),
        upBtn: document.getElementById("zone-list-up-btn"),
        downBtn: document.getElementById("zone-list-down-btn"),
      },
      {
        list: document.getElementById("channels"),
        upBtn: document.getElementById("channel-list-up-btn"),
        downBtn: document.getElementById("channel-list-down-btn"),
      }
    ];

    controls.forEach(({ list, upBtn, downBtn, acceptBtn }) => {
      if (!list) return;

      if (upBtn) {
        upBtn.addEventListener("click", () => {
          if (list.selectedIndex > 0) {
            list.selectedIndex -= 1;
            list.dispatchEvent(new Event("change"));
          }
        });
      }

      if (downBtn) {
        downBtn.addEventListener("click", () => {
          if (list.selectedIndex < list.options.length - 1) {
            list.selectedIndex += 1;
            list.dispatchEvent(new Event("change"));
          }
        });
      }

    });


  });
}

function _zoneList(){ openZoneModal();}

function _channelList() { openChannelModal();}


async function _btnChannelUp() {
  try {
    const nextChannel = await fetchNextChannel(config.activeZoneIndex, config.activeChannelNumber);
    updateConfig2(nextChannel);
    await switchTalkGroups(config.activeChannel.tgid);
  } catch (err) {
    console.error("Failed to go to next channel:", err);
    showAlert("Failed to go to next channel.");
  }
}

async function _btnChannelDown() {
  try {
    const previousChannel = await fetchPreviousChannel(config.activeZoneIndex, config.activeChannelNumber);
    updateConfig2(previousChannel);
    await switchTalkGroups(config.activeChannel.tgid);
  } catch (err) {
    console.error("Failed to go to previous channel:", err);
    showAlert("Failed to go to previous channel.");
  }
}

async function _btnZoneUp() {
  try {
    const next_zone = await fetchNextZone(config.activeZoneIndex);
    updateConfig(config.allZones, next_zone.zone_index, next_zone.channels[0].channel_number);
    await switchTalkGroups(next_zone.channels[0])
    updateUI();
  } catch (err) {
    console.error("Zone up error:", err);
    showAlert("Failed to go to next zone.");
  }
}

async function _btnZoneDown() {
  try {
    const prev_zone = await fetchPreviousZone(config.activeZoneIndex);
    updateConfig(config.allZones, prev_zone.zone_index, prev_zone.channels[0].channel_number);
    await switchTalkGroups(prev_zone.channels[0])
    updateUI();
  } catch (err) {
    console.error("Zone down error:", err);
    showAlert("Failed to go to previous zone.");
  }
}

/**
 * Update the configuration with the provided zones, zone index, and channel index.
 * @param {Array} zones - List of zones.
 * @param {number} zone_index - Index of the active zone.
 * @param {number} channel_index - Index of the active channel.
 */
function updateConfig(zones, zone_index, channel_index) {
  if (!zones[zone_index] || !zones[zone_index].channels[channel_index]) {
    console.error("Invalid zone or channel index in updateConfig");
    //console.log(zones, zone_index, channel_index)
    return;
  }
  
  config.allZones = zones;
  config.activeZoneIndex = zone_index;
  config.activeChannelIndex = channel_index;
  config.activeChannel = zones[zone_index].channels[channel_index];
  config.activeZoneName = zones[zone_index].name;
  config.activeChannelNumber = zones[zone_index].channels[channel_index].channel_number;
  config.activeZoneData = zones[zone_index];
  config.whitelist = zones[zone_index].channels[channel_index].tgid;

  console.log("Updated config:", config);

  updateUI();

}

function updateConfig2(channel) {
  if (channel.zone && channel.zone.name) {
    config.activeZoneName = channel.zone.name;
    config.activeZoneData = zones[channel.zone_index];

  } else {
    console.log("No value found.");
  }
  config.activeZoneIndex = channel.zone_index;
  config.activeChannelIndex = channel.channel_number;
  config.activeChannel = channel;
  config.activeChannelNumber = channel.channel_number;
  
  config.whitelist = channel.tgid;
  console.log("Updated config:", config);
  updateUI();
}

function findChannelIndex(zones, zone_index, channel_id) {
  for (let i = 0; i < zones[zone_index].channels.length; i++) {
      if (zones[zone_index].channels[i].id === channel_id) {
          return i;
      }
  }
  return -1; // Channel not found
}

/**
 * Update the UI elements with the current configuration.
 */
function updateUI() {
  updateElement('channel-number', config.activeChannelNumber.toString());
  updateElement('channel-name', config.activeChannel.name); 
  console.log("Active Zone", config.activeZoneName)
  updateElement('zone', config.activeZoneName);
}

function updateElement(id, text){
  const element = document.getElementById(id);
  if (element) {
    element.textContent = text;
  } else {
    console.error(`Element with ID ${id} not found.`);
  }
}

/**
 * Show the progress modal.
 */
function showProgressModal() {
  const modalEl = document.getElementById('progressModal');
  const progressBar = document.querySelector("#progress-display .progress-bar");
  const progressModal = new bootstrap.Modal(modalEl, {
    backdrop: 'static',
    keyboard: false
  });

  progressModal.show();
}

/**
 * Open the zone selection modal and populate it with zones.
 */
async function openZoneModal() {
  const zoneModalEl = document.getElementById('zoneModal');
  const zoneModal = new bootstrap.Modal(zoneModalEl, { backdrop: 'static', keyboard: false });
  zoneModal.show();

  try {
    // Assume config.allZones is an array of zone objects.
    const selectElement = document.getElementById('zones');
    selectElement.innerHTML = ""; // Clear existing options

    config.allZones.forEach((zone, index) => {
      const option = document.createElement('option');
      option.value = index;  // Use the zone index as the value
      option.textContent = `Zone ${index} - ${zone.name}`;
      if (index === config.activeZoneIndex) {
        option.selected = true;
      }
      selectElement.appendChild(option);
    });

    // Attach click listener to the Apply button.
    const zoneApplyBtn = document.getElementById('zone-list-accept-btn');
    zoneApplyBtn.onclick = async function () {
      try {
        const selectedZoneIndex = parseInt(selectElement.value);
        const firstChannel = config.allZones[selectedZoneIndex].channels[0];

        // Update configuration, update the UI, and switch talkgroups.
        updateConfig(config.allZones, selectedZoneIndex, firstChannel.channel_number);
        updateUI();
        zoneModal.hide();
        await switchTalkGroups(firstChannel.tgid);
      } catch (error) {
        console.error("Error setting zone:", error);
        alert("Error setting zone: " + error.message);
      }
    };
  } catch (error) {
    console.error("Error loading zones:", error);
    alert("Failed to load zones: " + error.message);
    zoneModal.hide();
  }
}

/**
 * Open the channel selection modal for a given zone index and populate it with channels.
 * @param {number} zone_index - Index of the zone to load channels from.
 */
async function openChannelModal() {
  const channelModalEl = document.getElementById('channelModal');
  const channelModal = new bootstrap.Modal(channelModalEl, { backdrop: 'static', keyboard: false });
  channelModal.show();

  try {
    // Use activeZoneData if available, otherwise use config.allZones at activeZoneIndex.
    const zone = config.activeZoneData || config.allZones[config.activeZoneIndex];
    if (!zone) throw new Error("Active zone not found");

    const channels = zone.channels || [];
    const selectElement = channelModalEl.querySelector('#channels');
    selectElement.innerHTML = ""; // Clear existing options

    channels.forEach(channel => {
      const option = document.createElement('option');
      option.value = channel.channel_number;
      option.textContent = `${channel.channel_number} - ${channel.name}`;
      if (channel.channel_number === config.activeChannelNumber) {
        option.selected = true;
      }
      selectElement.appendChild(option);
    });

    // Trigger selection when the accept button is clicked.
    const acceptBtn = channelModalEl.querySelector('#channel-list-accept-btn');
    acceptBtn.onclick = async function () {
      const selectedChannelNumber = parseInt(selectElement.value);
      const selectedChannel = channels.find(ch => ch.channel_number === selectedChannelNumber);
      if (!selectedChannel) {
        console.error("Channel not found in zone:", selectedChannelNumber);
        return;
      }
      try {
        updateConfig2(selectedChannel);
        updateUI();
        channelModal.hide();
        await switchTalkGroups(config.activeChannel.tgid);
      } catch (error) {
        console.error("Error setting channel:", error);
        alert("Error setting channel: " + error.message);
      }
    };
  } catch (error) {
    console.error("Error loading channels:", error);
    alert("Failed to load channels: " + error.message);
    channelModal.hide();
  }
}


/**
 * Scroll down through the list of buttons in the specified container.
 * @param {string} containerId - ID of the container element.
 */
function scrollDown(containerId) {
  const container = document.getElementById(containerId);
  if (!container) {
    console.error(`Container with id ${containerId} not found.`);
    return;
  }

  // Select only the list buttons (exclude any non-list buttons if needed)
  const buttons = container.querySelectorAll("button");
  if (!buttons || buttons.length === 0) {
    console.error(`No buttons found in container ${containerId}.`);
    return;
  }

  // Find the currently active button index.
  let activeIndex = -1;
  buttons.forEach((btn, index) => {
    if (btn.classList.contains("active-button")) {
      activeIndex = index;
    }
  });

  // If none active, select the first button.
  // Otherwise, move to the next button, wrapping around if needed.
  let newIndex = (activeIndex === -1) ? 0 : (activeIndex + 1) % buttons.length;

  // Remove active class from all buttons.
  buttons.forEach(btn => btn.classList.remove("active-button"));

  // Add active class to the new active button.
  const newActiveButton = buttons[newIndex];
  newActiveButton.classList.add("active-button");

  // Scroll the new active button into view.
  newActiveButton.scrollIntoView({ behavior: "smooth", block: "center" });
}

/**
 * Scroll up through the list of buttons in the specified container.
 * @param {string} containerId - ID of the container element.
 */
function scrollUp(containerId) {
  const container = document.getElementById(containerId);
  if (!container) {
    console.error(`Container with id ${containerId} not found.`);
    return;
  }

  const buttons = container.querySelectorAll("button");
  if (!buttons || buttons.length === 0) {
    console.error(`No buttons found in container ${containerId}.`);
    return;
  }

  // Find the currently active button index.
  let activeIndex = -1;
  buttons.forEach((btn, index) => {
    if (btn.classList.contains("active-button")) {
      activeIndex = index;
    }
  });

  // If none active, select the last button.
  // Otherwise, move to the previous button, wrapping around if needed.
  let newIndex = (activeIndex === -1) ? buttons.length - 1 : (activeIndex - 1 + buttons.length) % buttons.length;

  buttons.forEach(btn => btn.classList.remove("active-button"));

  const newActiveButton = buttons[newIndex];
  newActiveButton.classList.add("active-button");

  newActiveButton.scrollIntoView({ behavior: "smooth", block: "center" });
}

/**
 * Select a channel by name and update the UI.
 * @param {string} name - Name of the channel to select.
 */
function selectChannel(name) {
  toggleDisplay("channel-list"); // Ensure channel list is hidden
  toggleProgress(() => {
    document.getElementById('talkgroup').textContent = name;
    toggleDisplay('main-display');
  });
}

/**
 * Show an alert message in the alert container.
 * @param {string} message - The message to display.
 * @param {string} [type="danger"] - The type of alert (e.g., "success", "danger").
 */
function showAlert(message, type = "danger") {
  const container = document.getElementById("alert-container");
  if (!container) return;
  container.innerHTML = "";
  const alertDiv = document.createElement("div");
  alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
  alertDiv.setAttribute("role", "alert");
  alertDiv.textContent = message;
  const closeBtn = document.createElement("button");
  closeBtn.type = "button";
  closeBtn.className = "btn-close";
  closeBtn.setAttribute("data-bs-dismiss", "alert");
  closeBtn.setAttribute("aria-label", "Close");
  alertDiv.appendChild(closeBtn);
  container.appendChild(alertDiv);
  if (print_debug) console.log("ALERT:", message);
}

/**
 * Toggle the display of an element by its ID.
 * @param {string} elementId - The ID of the element to toggle.
 */
function toggleDisplay(elementId) {
  const el = document.getElementById(elementId);
  if (el) {
    el.classList.toggle("active");
  }
}

/**
 * Show the progress modal.
 */
function showProgressModal() {
  const modalEl = document.getElementById('progressModal');
  const modal = new bootstrap.Modal(modalEl, { backdrop: 'static', keyboard: false });
  modal.show();
}

/**
 * Hide the progress modal.
 */
function hideProgressModal() {
  const modalEl = document.getElementById('progressModal');
  const modal = bootstrap.Modal.getInstance(modalEl);
  if (modal) modal.hide();
}

/**
 * Toggle the progress indicator and execute a callback function.
 * @param {Function} callback - The callback function to execute.
 */
async function toggleProgress(callback) {
  // Show spinner if implemented
  try {
    await callback();
  } catch (error) {
    console.error("Error during progress:", error);
  } finally {
    // Hide spinner if implemented
  }
}

/**
 * Populate the zone list and highlight the current zone.
 */
async function populateZoneList() {
  try {
    const data = await fetchAllZones(); // Uses the new helper

    const zoneListContainer = document.getElementById("zones");
    zoneListContainer.innerHTML = "";

    const zones = data.zones || [];

    zones.forEach(zone => {
      const option = document.createElement("option");
      option.textContent = zone.name;
      option.setAttribute("data-zone_index", zone.zone_index);
      option.setAttribute("data-zone_name", zone.name);

      if (zone.name.toLowerCase() === currentZoneName?.toLowerCase()) {
        option.classList.add("active-item");
      }

      zoneListContainer.appendChild(option);
    });

  } catch (error) {
    console.error("Error fetching zones:", error);
    showAlert(error.message);
  }
}
const slider = document.getElementById("volumeRange");

function updateSliderColor(value) {
    console.log(value);
    let color;
    if (value < 33) {
        color = "red";
    } else if (value < 66) {
        color = "orange";
    } else {
        color = "green";
    }
  document.getElementById('volume_percent').textContent = value + "%";

    slider.style.setProperty('--thumb-color', color);
}


