import { API_BASE_URL, APIEndpoints, apiGet, apiPut } from "./api.js";

const print_debug = true; // or false, depending on your use case



function listenLogStream() {
  const source = new EventSource(API_BASE_URL + APIEndpoints.LOGGING.STREAM); // ✅ uses enum
  console.log("Listening to stream", "listenLogStream()")
  source.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      console.log('Log update:', data);

      const updateType = data.Action || data.Update;
      const tgName = data["Talkgroup Name"] || data.Talkgroup;

      if (updateType === 'voice update' && tgName) {
        const el = document.getElementById('talkgroup');
        if (el) el.textContent = tgName;
      }
    } catch (err) {
      console.warn("Invalid log stream data:", err);
    }
  };

  source.onerror = (err) => {
    console.error("SSE stream error:", err);
    source.close(); // optional: reconnect logic could go here
  };
  
}

// UI

function badge(badgeText, outerText, badgeClass = "badge badge-secondary") {
  return `<p><span class="${badgeClass}">${badgeText}</span> ${outerText}</p>`;
}

function showDynamicModal(title = "Dynamic Modal", bodyContent = "") {
  // Remove any existing modal
  const existing = document.getElementById("dynamicModal");
  if (existing) existing.remove();

  // Create modal wrapper
  const modal = document.createElement("div");
  modal.innerHTML = `
  <div class="modal fade" id="dynamicModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content">
              <div class="modal-header">
                  <h5 class="modal-title">${title}</h5>
                  <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
              </div>
              <div class="modal-body">
                  ${bodyContent}
              </div>
          </div>
      </div>
  </div>
  `;
  document.body.appendChild(modal);

  const bsModal = new bootstrap.Modal(modal.querySelector("#dynamicModal"));
  bsModal.show();
}

function updateNetworkModal(data) {
  if (!data) {
      console.warn("No network data provided");
      return;
  }

  const fieldMap = {
      'Status': data.Status,
      'WiFi Network': data['WiFi Network'],
      'Connection': data.Connection,
      'Memory': data.Memory,
      'CPU Temp': data['CPU Temp'],
      'Audio Output': data['Audio Output']
  };

  let bodyContent = "";

  for (const [label, value] of Object.entries(fieldMap)) {
      bodyContent += badge(label, value ?? "N/A");
  }

  showDynamicModal("Network Status", bodyContent);
}

async function updateUIFromChannel(channel) {
  updateElement('channel-number', channel.number);
  updateElement('channel-name', channel.name);

  try {
    const zone = await apiGet(APIEndpoints.SESSION.ZONE_CURRENT);
    updateElement('zone', zone.name);
  } catch (err) {
    console.warn("Could not fetch zone name for UI:", err);
    updateElement('zone', ""); // fallback if fetch fails
  }

}

async function updateUI() {
  //updateElement('channel-number', channel.number);
  //updateElement('channel-name', channel.name);

  try {
    const zone = await apiGet(APIEndpoints.SESSION.ZONE_CURRENT);
    const channel = await apiGet(APIEndpoints.SESSION.CHANNEL_CURRENT)
    updateElement('zone', zone.name);
    updateElement('channel-name', channel.name); 
    updateElement('channel-number', channel.channel_number);

  } catch (err) {
    console.warn("Could not fetch zone name for UI:", err);
    updateElement('zone', ""); // fallback if fetch fails
  }

}


async function _btnChannelDown() {
  try {
    const prevChannel = await apiPut(APIEndpoints.SESSION.CHANNEL_PREVIOUS);
    updateUIFromChannel(prevChannel);
  } catch (err) {
    console.error("Failed to go to previous channel:", err);
    showAlert("Failed to go to previous channel.");
  }
}

async function _btnChannelUp() {
  try {
    const nextChannel = await apiPut(APIEndpoints.SESSION.CHANNEL_NEXT);
    updateUIFromChannel(nextChannel);
  } catch (err) {
    console.error("Failed to go to next channel:", err);
    showAlert("Failed to go to next channel.");
  }
}

async function _btnZoneUp() {
  try {
    const nextZone = await apiPut(APIEndpoints.SESSION.ZONE_NEXT);
    const firstChannel = nextZone.channels?.[0];
    if (!firstChannel) throw new Error("No channels in next zone.");
    updateUIFromChannel(firstChannel);
  } catch (err) {
    console.error("Zone up error:", err);
    showAlert("Failed to go to next zone.");
  }
}

async function _btnZoneDown() {
  try {
    const prevZone = await apiPut(APIEndpoints.SESSION.ZONE_PREVIOUS);
    const firstChannel = prevZone.channels?.[0];
    if (!firstChannel) throw new Error("No channels in previous zone.");
    updateUIFromChannel(firstChannel);
  } catch (err) {
    console.error("Zone down error:", err);
    showAlert("Failed to go to previous zone.");
  }
}

async function openZoneModal() {
  const zoneModalEl = document.getElementById('zoneModal');
  const zoneModal = new bootstrap.Modal(zoneModalEl, { backdrop: 'static', keyboard: false });
  zoneModal.show();

  try {
    const zones = await apiGet(APIEndpoints.ZONES.LIST);
    const selectElement = document.getElementById('zones');
    selectElement.innerHTML = "";

    Object.entries(zones).forEach(([index, zone]) => {
      const option = document.createElement('option');
      option.value = index;
      option.textContent = `Zone ${index} - ${zone.name}`;
      selectElement.appendChild(option);
    });

    document.getElementById('zone-list-accept-btn').onclick = async function () {
      try {
        const selectedZoneIndex = selectElement.value;
    
        await apiPut(APIEndpoints.SESSION.ZONE_SELECT(selectedZoneIndex)); // sets new zone + channel
    
        const zone = await apiGet(APIEndpoints.SESSION.ZONE_CURRENT);
        updateElement('zone', zone.name);
    
        const channel = await apiGet(APIEndpoints.SESSION.CHANNEL_CURRENT);
        updateUIFromChannel(channel);
    
        zoneModal.hide();
      } catch (error) {
        console.error("Error applying zone:", error);
        alert("Failed to apply selected zone.");
      }
    };

  } catch (err) {
    console.error("Error loading zones:", err);
    alert("Failed to load zones.");
    zoneModal.hide();
  }
}

async function openChannelModal() {
  const channelModalEl = document.getElementById('channelModal');
  const channelModal = new bootstrap.Modal(channelModalEl, { backdrop: 'static', keyboard: false });
  channelModal.show();

  try {
    // ✅ Get the current zone from session
    const zone = await apiGet(APIEndpoints.SESSION.ZONE_CURRENT);
    const channels = zone.channels || {};
    const selectElement = channelModalEl.querySelector('#channels');
    selectElement.innerHTML = ""; // Clear existing options

    Object.entries(channels).forEach(([channelNum, channel]) => {
      const option = document.createElement('option');
      option.value = channelNum;
      option.textContent = `${channelNum} - ${channel.name}`;
      selectElement.appendChild(option);
    });

    // ✅ Accept button listener
    const acceptBtn = channelModalEl.querySelector('#channel-list-accept-btn');
    acceptBtn.onclick = async function () {
      const selectedChannelNumber = selectElement.value;

      try {
        await apiPut(APIEndpoints.SESSION.CHANNEL_SELECT(selectedChannelNumber));
        updateUI();
        channelModal.hide();
      } catch (error) {
        console.error("Error setting channel:", error);
        alert("Failed to set channel.");
      }
    };

  } catch (error) {
    console.error("Error loading channels:", error);
    alert("Failed to load channels.");
    channelModal.hide();
  }
}

async function fetchNetworkInfo() {
  try {
      const data = await apiGet(APIEndpoints.CONFIG.HOSTS);

      const adminURL = `${data.lan_ip}/utilities/index.html`;
      const qrCodeSource = API_BASE_URL + APIEndpoints.UTILITIES.QR_CODE(adminURL);
      document.getElementById('adminPanelQR').src = qrCodeSource;

      if (data.localhost) document.getElementById('localhost').textContent = data.localhost;
      if (data.hostname) document.getElementById('hostname').textContent = data.hostname;
      if (data.fqdn) document.getElementById('fqdn').textContent = data.fqdn;
      if (data.lan_ip) document.getElementById('lan_ip').textContent = data.lan_ip;
  } catch (err) {
      console.error("Failed to fetch network info:", err.message);
  }
}

async function fetchNetworkStatus() {
  try {
      const data = await apiGet(APIEndpoints.NETWORK);
      updateNetworkModal(data);
  } catch (err) {
      console.error("Failed to fetch network status:", err.message);
  }
}

async function sendVolume(level) {
  try {
    const response = await fetch(`${API_BASE_URL}${APIEndpoints.VOLUME.SET(level)}`, {
      method: "PUT",
      credentials: "include"
    });

      if (!response.ok) {
          const error = await response.text();
          throw new Error(`Volume API error: ${error}`);
      }

      const data = await response.json();
      console.log(JSON.stringify(data, null, 2));
  } catch (err) {
      console.error("Failed to set volume:", err.message);
  }
}
async function fetchCurrentVolume() {
  try {
    const response = await fetch(`${API_BASE_URL}${APIEndpoints.VOLUME.GET_SIMPLE}`);
      if (!response.ok) {
          const error = await response.text();
          throw new Error(`Volume fetch error: ${error}`);
      }

      const data = await response.text(); 
      document.getElementById("volumeRange").value = data;
      updateSliderColor(data);
  } catch (err) {
      console.error("Error getting volume:", err.message);
  }
}

async function populateZoneList() {
  try {
      const zones = await apiGet(APIEndpoints.ZONES.LIST);

      const zoneListContainer = document.getElementById("zones");
      zoneListContainer.innerHTML = "";

      Object.entries(zones).forEach(([index, zone]) => {
          const option = document.createElement("option");
          option.textContent = zone.name;
          option.setAttribute("data-zone_index", index);
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

function selectChannel(name) {
  toggleDisplay("channel-list");

  toggleProgress(() => {
      const talkgroupEl = document.getElementById('talkgroup');
      if (talkgroupEl) talkgroupEl.textContent = name;

      toggleDisplay('main-display');
  });
}

 
function _zoneList(){ openZoneModal();}
  
function _channelList() { openChannelModal();}

async function _channelApplyBtn() {
  const selectElement = document.getElementById('channels');
  if (!selectElement) {
      console.error("Channel select element not found");
      return;
  }

  const selectedChannelNumber = parseInt(selectElement.value);
  if (isNaN(selectedChannelNumber)) {
      console.error("Invalid channel number selected");
      return;
  }

  try {
      // Use the new PUT endpoint to update session to the selected channel
      const channel = await apiPut(APIEndpoints.SESSION.CHANNEL_SELECT(selectedChannelNumber));

      // Update UI with response
      updateElement('channel-number', channel.number);
      updateElement('channel-name', channel.name);

      const zone = await apiGet(APIEndpoints.SESSION.ZONE_CURRENT); // get current zone
      updateElement('zone', zone.name);

      // ✅ Close the modal safely using Bootstrap API
      const modalEl = document.getElementById('channelModal');
      const modalInstance = bootstrap.Modal.getInstance(modalEl);
      if (modalInstance) modalInstance.hide();

  } catch (error) {
      console.error("Error setting channel:", error);
      alert("Error setting channel: " + error.message);
  }
}

function updateSliderColor(value) {
  console.log("Volume slider value:", value);

  const slider = document.getElementById("volumeRange");
  const volumeLabel = document.getElementById("volume_percent");

  if (!slider || !volumeLabel) {
      console.warn("Slider or volume label not found.");
      return;
  }

  let color = "green";
  if (value < 33) {
      color = "red";
  } else if (value < 66) {
      color = "orange";
  }

  volumeLabel.textContent = `${value}%`;
  slider.style.setProperty('--thumb-color', color);
}

function updateElement(id, text) {
  const element = document.getElementById(id);

  if (!element) {
      console.warn(`updateElement: No element found with ID "${id}"`);
      return;
  }

  element.textContent = text ?? "";
}

/** Initialize volume slider and input coloring */
function setupVolumeControls() {
  const volumeSlider = document.getElementById("volumeRange");
  if (!volumeSlider) {
      console.error("Volume slider not found.");
      return;
  }

  volumeSlider.addEventListener("change", () => {
      sendVolume(volumeSlider.value);
  });

  volumeSlider.addEventListener("input", () => {
      updateSliderColor(volumeSlider.value);
  });
}

/** Initialize Wi-Fi icon click for fetching network status */
function setupNetworkIcon() {
  const wifiIcon = document.getElementById("wifi-icon");
  if (wifiIcon) {
      wifiIcon.addEventListener("click", fetchNetworkStatus);
  } else {
      console.warn("WiFi icon not found.");
  }
}

/** Hook up all zone/channel buttons */
function setupZoneAndChannelButtons() {
  const buttonMap = [
      { id: "btnZoneList", handler: openZoneModal },
      { id: "btnChannelList", handler: _channelList },
      { id: "btnZoneUp", handler: _btnZoneUp },
      { id: "btnZoneDown", handler: _btnZoneDown },
      { id: "btnChannelUp", handler: _btnChannelUp },
      { id: "btnChannelDown", handler: _btnChannelDown }
      // { id: "channel-apply", handler: _channelApplyBtn }
  ];

  buttonMap.forEach(({ id, handler }) => {
      const el = document.getElementById(id);
      if (el) {
          el.addEventListener("click", handler);
      } else {
          console.warn(`Element not found: ${id}`);
      }
  });
}



document.addEventListener("DOMContentLoaded", async () => {
  
  console.log("DOMContentLoaded", "interface.js");
  
  // CONSTANTS
  
  document.getElementById('status-network-info').addEventListener("click", () => {
      fetchNetworkInfo();
      console.log("addEventListener", "status-network-info")
  });

  listenLogStream();
  await updateUI();
  
  setupVolumeControls();
  // setupNetworkIcon();
  setupZoneAndChannelButtons();
  fetchCurrentVolume();
});
