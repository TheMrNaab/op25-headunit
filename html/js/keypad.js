// Initialize keypad listeners after DOM is fully loaded.
document.addEventListener("DOMContentLoaded", initializeKeypadListeners);

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
  

  function showKeypadModal() {
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

function handleDelete(event){
  const channelInput = document.getElementById("channel_text");
  channelInput.value = channelInput.value.slice(0, -1);

    if(exceedsChannelLimit()){
        btnGo.setAttribute("disabled", "true");

    } else {
        btnGo.removeAttribute("disabled");
    }

}

function handleKeypadKeyPress(event) {
  // Use event.currentTarget to reference the button that received the event.
  const btn = event.currentTarget;

  if (btn.disabled) return;
  
  const channelInput = document.getElementById("channel_text");
  const digit = btn.getAttribute("data-value");
  let currentValue = channelInput.value;
  const zone_max = config.activeZoneData.length;

  const MAX_LENGTH = parseInt(channelInput.getAttribute("maxlength"), 10);
  
  if (currentValue.length <= MAX_LENGTH) {
    channelInput.value = currentValue + digit;
  } else {
    // When at max length, remove the first character and append the new digit.
    channelInput.value = currentValue.substring(1) + digit;
  }

  btnGo = document.getElementById("go-btn");
  exceeds = exceedsChannelLimit(digit);
  if(exceeds){
    btnGo.setAttribute("disabled", "true");
  } else {
    btnGo.removeAttribute("disabled");
  }
}

function exceedsChannelLimit() {
  const val = document.getElementById("channel_text").value;
  const numberOfChannels = config.activeZoneData.channels.length;

  text_number = parseInt(val, 10);
  er = document.getElementById("channel_error");
  
  if (text_number > numberOfChannels) {
    er.innerHTML = "Channel number exceeds maximum of " + numberOfChannels; 
    return true;
  } else {
    er.innerHTML = ""; 
  }

  return false;

}

function submitChannel(channel) {
  console.log("submitChannel()")
  // This is the placeholder function for channel submission.
  // Replace the console.log with your API call or channel switching logic.
  whitelist(channel);
  hideKeypadModal();
  updateUI();
  console.log("Channel submitted:", channel);
  channelEntryTimer = null;
}