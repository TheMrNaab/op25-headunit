// INTERFACE.JS
import { API_BASE_URL, APIEndpoints, apiGet, apiPut, apiGetV2 } from "./api.js";
let keypadZone = {};
let keypadZones = {};
let channelCount = 0;
let selectedValue = -1;
const print_debug = true; // or false, depending on your use case

async function fetchTalkgroupName(tgid) {
  const response = await fetch(`/session/talkgroups/${tgid}/name/plaintext`);
  if (response.ok) {
    const data = await response.json();
    document.getElementById('talkgroup-name').textContent = data.name;
  } else {
    console.error('Error fetching talkgroup name');
  }
}

function listenLogStream() {
  const source = new EventSource(API_BASE_URL + APIEndpoints.LOGGING.STREAM);
  console.log("Listening to stream", "listenLogStream()");
  source.onmessage = async (event) => {
    try {
      const data = JSON.parse(event.data);
      console.log("Log update:", data);

      const updateType = data.Action || data.Update;
      const tgid = data["Talkgroup"] || -1;
      if (updateType === "voice update" && tgid !== -1) {
        try {
          const response = await fetch(API_BASE_URL + APIEndpoints.SESSION.TALKGROUP_NAME(tgid));
          const jsonData = await response.json();
          const el = document.getElementById("talkgroup");
          if (el) el.textContent = jsonData.name;
        } catch (fetchError) {
          console.error("Error fetching talkgroup name:", fetchError);
        }
      }
    } catch (parseError) {
      console.warn("Invalid log stream data:", parseError);
    }
  };

  source.onerror = (err) => {
    console.warn("SSE stream error:", err);
  };
}

// UI
function showDynamicModal(title = "Dynamic Modal", bodyContent = "", footerContent = "") {
  // Remove any existing modal
  var footerHTML = ""
  const existing = document.getElementById("dynamicModal");
  if (existing) existing.remove();

  // Create footer if content is provided
  if (footerContent != "") {
    footerHTML = `<div class="modal-footer">
      ${footerContent}
      </div>`;
  }



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
              <div class="modal-body text-start">
                  ${bodyContent}
              </div>
            ${footerHTML}
          </div>
      </div>
  </div>
  `;
  document.body.appendChild(modal);

  const bsModal = new bootstrap.Modal(modal.querySelector("#dynamicModal"));
  bsModal.show();
}

async function gitHubDialog() {
  const qrcode = `http://${location.hostname}:5001/utilities/qrcode/https://github.com/TheMrNaab/op25-headunit`;
  const image = `<img src="${qrcode}" alt="QR Code" class="img-fluid" style="max-width: 200px; max-height: 200px;">`;
  const bodyContent = `
      <div class="text-center">
          <p>Scan the QR Code to access the GitHub repository</p>
          ${image}
          <p><a href="${qrcode}" target="_blank">github.com/TheMrNaab/op25-headunit</a></p>
      </div>`;
  showDynamicModal("Github Information", bodyContent);
}

async function updateNetworkModal(data) {
  if (!data) {
    console.warn("No network data provided");
    return;
  }

  var audio_req = await apiGetV2(APIEndpoints.DEVICE.GET_AUDIO_PROPERTY("api.alsa.path"));
  var response = await audio_req.json();

  const fieldMap = {
    'Audio Output': response['api.alsa.path'],
    'Connection Type': data.connection_type,
    'Network Device': data.wifi_name,
    'CPU Temp': data.cpu_temp,
    'Memory': data.mem_available,
    'Status': data.status,
    'Host Name': data.host_name,
    'Host IP': data.host_ip,
    'HTTP Port': data.host_port,
    'Web Interface': `http://${data.host_ip}:${data.host_ip}/admin/index.html`
  };

  let bodyContent = "";
  let collection = [];
  bodyContent = `<p><textarea style="width:100%; height: 300px; background-color: #f8f9fa; border: 1px solid #ced4da; border-radius: 0.25rem; padding: 10px; font-family: monospace; font-size: 14px;" readonly>`;
  for (const [label, value] of Object.entries(fieldMap)) {
    bodyContent += `${label}: ${value}\n`
  }

  bodyContent += `</textarea></p>`

  // TODO: Implement Restart System
  var footerContent = `<button class="btn btn-warning" onClick="reloadSystem()" disabled><i class="fas fa-refresh me-1"></i>Reload System</button>`;
  footerContent += `<p class=text-center><button class="btn btn-secondary" onClick="window.open('http://${data.host_ip}:${data.host_port}/admin/index.html', '_blank')"><i class="fas fa-external-link-alt me-1"></i>Open Web Interface</button></p>`;
  showDynamicModal("Device Status", bodyContent, footerContent);
}

function createBootstrapRow(...elements) {
  const rowDiv = document.createElement("div");
  rowDiv.className = "row";

  elements.forEach((element) => {
    if (element instanceof HTMLElement) {
      rowDiv.appendChild(element);
    } else {
      console.warn("Invalid element provided, skipping:", element);
    }
  });

  return rowDiv;
}

function createBootstrapCol(size, ...elements) {
  const colDiv = document.createElement("div");
  colDiv.className = `col-${size}`;

  elements.forEach((element) => {
    if (element instanceof HTMLElement) {
      colDiv.appendChild(element);
    } else {
      console.warn("Invalid element provided, skipping:", element);
    }
  });

  return colDiv;
}

function createP(text, className = "") {
  const p = document.createElement("p");
  p.textContent = text;
  if (className) {
    p.className = className;
  }
  return p;
}

function badge(badgeText, outerText, badgeClass = "badge rectangle-pill bg-secondary") {
  const p = document.createElement("p");

  const span = document.createElement("span");
  span.className = badgeClass;
  span.textContent = badgeText;

  p.appendChild(span);
  p.appendChild(document.createTextNode(" " + outerText));

  return p;
}

async function updateUI() {
  try {
    const zone = await apiGet(APIEndpoints.SESSION.ZONE_CURRENT);
    const channel = await apiGet(APIEndpoints.SESSION.CHANNEL_CURRENT)


    console.log("zone", zone);
    console.log("channel", channel);
    
    updateElement('zone', zone.name);
    updateElement('channel-name', channel.name);
    updateElement('channel-number', channel.channel_number);
    updateElement('talkgroup', ''); // NOTE: BLANK BECAUSE WE HAVE NO CALL YET

  } catch (err) {
    console.warn("Could not fetch zone name for UI:", err);
    updateElement('zone', ""); // fallback if fetch fails
  }

}

async function _btnChannelDown() {
  try {
    const prevChannel = await apiPut(APIEndpoints.SESSION.CHANNEL_PREVIOUS);
    updateUI();
  } catch (err) {
    console.error("Failed to go to previous channel:", err);
    showAlert("Failed to go to previous channel.");
  }
}

async function _btnChannelUp() {
  try {
    const nextChannel = await apiPut(APIEndpoints.SESSION.CHANNEL_NEXT);
    updateUI();
  } catch (err) {
    console.error("Failed to go to next channel:", err);
    showAlert("Failed to go to next channel.");
  }
}

async function _btnZoneUp() {
  try {
    const response = await apiPut(APIEndpoints.SESSION.ZONE_NEXT);
    if (!response) throw new Error("Unable to advance to the previous zone.");
    updateUI();
  } catch (err) {
    console.error("Zone up error:", err);
    showAlert("Failed to go to next zone.");
  }
}

async function _btnZoneDown() {
  try {
    const response = await apiPut(APIEndpoints.SESSION.ZONE_PREVIOUS);
    if (!response) throw new Error("Unable to advance to next zone.");
    updateUI();
  } catch (err) {
    console.error("Zone down error:", err);
    showAlert("Failed to go to previous zone.");
  }
}

async function openZoneModal() {
  const zoneModalEl = document.getElementById('zoneModal');
  const zoneModal = new bootstrap.Modal(zoneModalEl, { backdrop: 'static', keyboard: false });

  try {
    // Fetch the list of zones
    const response = await apiGetV2(APIEndpoints.ZONES.LIST);

    // Parse the response as JSON
    const data = await response.json();

    // Debugging: Log the parsed zones
    console.log("Parsed Zones:", data);

    // Access the zones array
    const zones = Object.values(data.zones);

    // Populate the dropdown
    const selectElement = document.getElementById('zones');
    selectElement.innerHTML = ""; // Clear existing options

    zones.forEach((zone) => {
      const option = document.createElement('option');
      option.value = zone.zone_index;
      option.textContent = `Zone ${zone.zone_index} - ${zone.name || "undefined"}`;
      selectElement.appendChild(option);
    });

    // Show the modal
    zoneModal.show();

    // Handle the accept button click
    document.getElementById('zone-list-accept-btn').onclick = async function () {
      try {
        console.log("Select Field Element:", selectElement)
        console.log("Selected zone index:", selectElement.value);

        const selectedZoneIndex = selectElement.value;

        // Set the new zone
        await apiPut(APIEndpoints.SESSION.ZONE_SELECT(selectedZoneIndex));

        // Update the UI
        updateUI();

        // Hide the modal
        zoneModal.hide();
      } catch (error) {
        console.error("Error applying zone:", error);
        alert("Failed to apply selected zone.");
      }
    };
  } catch (error) {
    console.error("Error loading zones:", error);
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

document.addEventListener("DOMContentLoaded", () => {
  const select = document.getElementById("zones");
  const upBtn = document.getElementById("zone-list-up-btn");
  const downBtn = document.getElementById("zone-list-down-btn");

  upBtn.addEventListener("click", () => {
    if (select.selectedIndex > 0) {
      select.selectedIndex -= 1;
    }
  });

  downBtn.addEventListener("click", () => {
    if (select.selectedIndex < select.options.length - 1) {
      select.selectedIndex += 1;
    }
  });
});

// channel-list-up-btn
// channel-list-down-btn

document.addEventListener("DOMContentLoaded", () => {
  const select = document.getElementById("channels");
  const upBtn = document.getElementById("channel-list-up-btn");
  const downBtn = document.getElementById("channel-list-down-btn");

  upBtn.addEventListener("click", () => {
    if (select.selectedIndex > 0) {
      select.selectedIndex -= 1;
    }
  });

  downBtn.addEventListener("click", () => {
    if (select.selectedIndex < select.options.length - 1) {
      select.selectedIndex += 1;
    }
  });
});

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
    console.log("Loading Populate Zones")
    console.log(zones);

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


function _zoneList() { openZoneModal(); }

function _channelList() { openChannelModal(); }

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


let config = {};
let configuration_json = config;



async function LoadKeypadFunctions() {
  console.log("LoadKeypadFunctions() CALLED");  // ✅ Add this
    try {
    const configuration_response = await fetch(`http://${location.hostname}:5001/admin/config/get`);
    if (!configuration_response.ok) {
      console.error("Failed to fetch configuration");
      return;
    }

    const configuration_json = await configuration_response.json();

    // Debugging: Log the parsed configuration
    console.log("Configuration Loaded: ", configuration_json['FN']); // not btn1_name directly

    // SET INITIAL BUTTON VALUES
    document.getElementById("btnFunction1Input").value = parseInt(configuration_json['FN'].btn1_zone) + 1;
    document.getElementById("btnFunction2Input").value = parseInt(configuration_json['FN'].btn2_zone) + 1;
    document.getElementById("btnFunction3Input").value = parseInt(configuration_json['FN'].btn3_zone) + 1;
    
    document.getElementById("btnFunction1Input").setAttribute("data-shortname", configuration_json['FN'].btn1_name);
    document.getElementById("btnFunction2Input").setAttribute("data-shortname", configuration_json['FN'].btn2_name);
    document.getElementById("btnFunction3Input").setAttribute("data-shortname", configuration_json['FN'].btn3_name);
    
    document.getElementById("btnFunction1Input").checked = true;
    // ADD ZONE ID TO INPUTS
    document.getElementById("btnFunction1").innerText = configuration_json['FN'].btn1_name;
    document.getElementById("btnFunction2").innerText = configuration_json['FN'].btn2_name;
    document.getElementById("btnFunction3").innerText = configuration_json['FN'].btn3_name;
    
    // DISABLE INPUT THAT HAVE A VALUE OF -1
    if(configuration_json['FN'].btn1_zone == -1) {document.getElementById("btnFunction1Input").setAttribute("disabled", "true");}
    if(configuration_json['FN'].btn2_zone == -1) {document.getElementById("btnFunction2Input").setAttribute("disabled", "true");}
    if(configuration_json['FN'].btn3_zone == -1) {document.getElementById("btnFunction3Input").setAttribute("disabled", "true");}
    
    // SET BUTTON GROUP ON CHANGE EVENT
    document.querySelectorAll('input[name="zoneSelection"]').forEach(el => {
      el.addEventListener("change", onZoneChange);
    });
    onZoneChange(null);
    // REMINDER: zoneSelection is the input group
    // SET GLOBAL VALUE
    window.configuration_json = configuration_json;



  } catch (err) {
    console.error("Error loading zones:", err);
  }
}

// TODO: FIX UI
// TODO: LOAD ZONES INTO VARIABLE
// * AS WE TYPE, WE USE THAT ZONE TO DETERMINE MAX CHANNEL
//  - WE ALSO SET keypadZoneName TO THE ZONE NAME


async function onZoneChange(event) {

  const response = await fetch(`http://${location.hostname}:5001/zones`);
  keypadZones = await response.json();

  selectedValue = parseInt(document.querySelector('input[name="zoneSelection"]:checked').value, 10);
  keypadZone = keypadZones['zones'][selectedValue];
  console.log("Set Keypad Zone > ", keypadZone)

  // Set the maximum length for the input field based on the selected zone
  channelCount = keypadZone.channels.length;

  document.getElementById('keypadZoneName').innerText = keypadZone.name;

  document.querySelectorAll('input[name="zoneSelection"]').forEach(el => {
    // SET THE KEYPAD ZONE NAME TO THE BUTTON'S ZONE NAME
    if(el.value == selectedValue) {
      document.getElementById('keypadZoneName').innerText = el.getAttribute("data-shortname");
    }
  });

  console.log("Selected Value:", selectedValue);
  console.log("Fetched Zones:", keypadZones.zones);
  console.log("Active Zone:", keypadZone);
}

function initializeKeypadListeners() {
  console.log("Init Keys")
  // Retrieve the maximum length from the input's max attribute.
  const MAX_LENGTH = parseInt(document.getElementById("channel_text").getAttribute("max"), 10);
  const channelInput = document.getElementById("channel_text");
  if (!channelInput) {
    console.error("Element with id 'channel_text' not found.");
    return;
  }

  // Select all keypad buttons that have a data-value attribute.
  const keypadButtons = document.querySelectorAll(".keypad-btn[data-value]");


  async function showKeypadModal() {
    await LoadKeypadFunctions();
    const keypadModalEl = document.getElementById('keypadModal');
    const keypadModal = new bootstrap.Modal(keypadModalEl, { backdrop: 'static', keyboard: false });
    keypadModal.show();
  }

  function hideKeypadModal() {
    const modalEl = document.getElementById('keypadModal');
    const modalInstance = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
    modalInstance.hide();
  }

  const delButton = document.getElementById("del-btn");
  delButton.addEventListener("click", handleDelete);

  keypadButtons.forEach(button => {
    button.addEventListener("click", handleKeypadKeyPress);
  });
}

function handleDelete(event) {
  const btnGo = document.getElementById("go-btn");
  const channelInput = document.getElementById("channel_text");
  channelInput.value = channelInput.value.slice(0, -1);

  playButton("Delete");
  if (exceedsChannelLimit()) {
    btnGo.setAttribute("disabled", "true");

  } else {
    btnGo.removeAttribute("disabled");
  }

}

async function btnGo_click(event){
  let channel_text = document.getElementById("channel_text").value;
  let zn = parseInt(keypadZone.zone_index, 10);
  console.log("zn: ", keypadZone.zone_index);
  let ch = parseInt(channel_text, 10) - 1; // Correct for offset
  let url = `/session/zone/${zn}/channel/${ch}`;
  console.log("btnGo_click()", url);
}

function getActualChannelNumber(ch) {
  // THIS FUNCTION SUBTRACTS 1 FROM THE CHANNEL NUMBER
  // SINCE THE CHANNEL INDEX STARTS AT 0
  // KEEP THIS FUNCTION FOR PURPOSE OF CLARITY
  return parseInt(ch, 10) - 1;
}

function handleKeypadKeyPress(event) {
  const btn = event.currentTarget;
  
  if (btn.disabled) return;
  
  const digit = btn.getAttribute("data-value");
  const channelInput = document.getElementById("channel_text");
  
  let currentRaw = channelInput.value.trim();
  
  console.log("***")
  console.log("Digit Pressed: ", digit);
  console.log("Channel Input: ", currentRaw);

  let currentValue = Number.isNaN(parseInt(currentRaw, 10)) ? 0 : parseInt(currentRaw, 10);
  
  // If the raw value is blank, we will assign it the digit pressed
  if(currentRaw == "") { currentRaw = digit; }

  // Channels are indexed at Zero, but they should begin at 1
  // We will correct this by subtracting 1 from the channel number
  let nextChannelNumber = parseInt(`${currentValue}${digit}`, 10) - 1;
  console.log("Next Channel Number", nextChannelNumber);
  playButton(digit);

  if (nextChannelNumber + 1 < channelCount) {
    channelInput.value = nextChannelNumber + 1; // +1 to match the display
    const nextChannel = keypadZone["channels"][nextChannelNumber];
    document.getElementById("keypadZoneName").innerText = nextChannel?.name || "Invalid";
  } else {
    // Fallback: append digit to raw string if logic fails
    channelInput.value = currentRaw;
  }

  const btnGo = document.getElementById("go-btn");
  const exceeds = exceedsChannelLimit(nextChannelNumber, channelCount);
  console.log("Exceeds Limit", exceeds);
  if (exceeds) {
    btnGo.setAttribute("disabled", "true");
  } else {
    btnGo.removeAttribute("disabled");
  }
  console.log("***")
}

function playButton(id){
  const audio = new Audio(`audio/${id}.m4a`);
  audio.play();
  audio.volume = 0.2;
}

function exceedsChannelLimit(strLength, channelCount) {
  const val = document.getElementById("channel_text").value;

  let text_number = parseInt(val, 10);
  let er = document.getElementById("channel_error");

  if (strLength > channelCount) {
    er.innerHTML = "Channel number exceeds maximum of " + channelCount;
    return true;
  } else {
    er.innerHTML = "";
  }

  return false;

}

function submitChannel(channel) {
  console.log("submitChannel()")
  const channelInput = document.getElementById("channel_text");
  response = fetch(`http://${location.hostname}:5001/session/channel/${channelInput}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ channel: channel })
  });

  if (!response.ok) {
    console.error("Failed to submit channel:", response.statusText); // PLACE ERROR ON KEYBOARD
    return;
  }

  hideKeypadModal();
  updateUI();
  channelEntryTimer = null;
}


document.addEventListener("DOMContentLoaded", async () => {
  console.log("DOMContentLoaded", "interface.js");
  document.getElementById('status-network-info').addEventListener("click", () => {
    fetchNetworkStatus();
  });
  document.getElementById('status-github-info').addEventListener("click", () => {
    gitHubDialog();
  });

  document.getElementById('go-btn').addEventListener("click", btnGo_click);
  

  listenLogStream();
  await updateUI();
  setupVolumeControls();
  setupZoneAndChannelButtons();
  initializeKeypadListeners()
  fetchCurrentVolume();
  await LoadKeypadFunctions(); 
});