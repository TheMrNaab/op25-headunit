const API_BASE_URL = `http://${location.hostname}:5001`;

document.addEventListener('DOMContentLoaded', async function () {
  await loadServerData();
});

// SYSTEMS.HTML //
/* 

EXAMPLE JSON INPUT/OUTPUT

{
  "0": {
    "blacklist": null,
    "center_frequency": null,
    "control_channels": [
      853.15,
      853.4625,
      853.925,
      853.9625
    ],
    "modulation": null,
    "nac": "0x000",
    "offset": 0,
    "sysname": "Wake County Simulcast",
    "tgid_tags_file": null,
    "whitelist": null
  },
  "1": {
    "blacklist": null,
    "center_frequency": null,
    "control_channels": [
      853.46,
      853.3625,
      853.25,
      853.525
    ],
    "modulation": null,
    "nac": "0x000",
    "offset": 0,
    "sysname": "Wake County Simulcast II FAKE",
    "tgid_tags_file": null,
    "whitelist": null
  }
}
*/

function postJSON() {
  const payload = {};

  records.forEach((record, index) => {
    const system = {};

    system["sysid"] = record["sysid"];
    system["sysname"] = record["sysname"];
    system["control_channels"] = Array.isArray(record["control_channels"])
      ? record["control_channels"]
      : (record["control_channels"] || "").split(',')
          .map(f => parseFloat(f.trim()))
          .filter(f => !isNaN(f));
    system["offset"] = record["offset"];
    system["nac"] = record["nac"];
    system["modulation"] = record["modulation"];
    system["tgid_tags_file"] = record["tgid_tags_file"];
    system["whitelist"] = record["whitelist"];
    system["blacklist"] = record["blacklist"];
    system["center_frequency"] = record["center_frequency"];
    system["index"] = index;

    payload[index] = system;
  });

  console.log("Confirming save playload", payload);

  

  fetch(`${API_BASE_URL}/admin/systems/update`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload, null, 2)
  })
  .then(response => {
    if (response.ok) {
      alert('Configuration saved successfully.');
    } else {
      alert('Failed to save configuration.');
    }
  })
  .catch(error => {
    console.error('Fetch error:', error);
    alert('Error saving configuration.');
  });
}

const fullFields = [
  "Sysid",
  "Sysname",
  "Control Channel List",
  "Offset",
  "NAC",
  "Modulation",
  "TGID Tags File",
  "Whitelist",
  "Blacklist",
  "Center Frequency"
];


function handleImport() {
  const file = document.getElementById('fileInput').files[0];
  if (!file) return alert("Please select a file.");

  const reader = new FileReader();
  reader.onload = () => {
    parseRRCSV(reader.result);
    const importModalEl = document.getElementById('importModal');
    const modal = bootstrap.Modal.getInstance(importModalEl);
    modal.hide();
  };
  reader.readAsText(file);
}

function parseRRCSV(text) {
  const lines = text.trim().split(/\r?\n/);
  const header = lines[0].split(',').map(h => h.trim());
  const data = [];

  for (let i = 1; i < lines.length; i++) {
    const row = lines[i].split(',').map(cell => cell.trim());
    if (row.length < header.length) continue;

    const base = {};
    header.forEach((key, idx) => base[key] = row[idx]);

    const freqs = row.slice(header.length); // Remaining columns after header
    const controlFreqs = freqs
      .filter(f => f.toUpperCase().endsWith('C'))
      .map(f => parseFloat(f.replace(/c$/i, '').trim()))
      .filter(f => !isNaN(f)); // Final array of numbers

    if (controlFreqs.length === 0) continue;
    console.log(base);
    const record = {
      "sysid": base["Hex"] || "",
      "sysname": (base["Description"] || "Unknown").replace(/"/g, '').trim(),
      "control_channels": controlFreqs,              // ✅ store as array of numbers
      "offset": "",
      "nac": base["Site NAC"] || "",
      "modulation": "",
      "tgid_tags_file": null,
      "whitelist": null,
      "blacklist": null,
      "center_frequency": ""
    };

    data.push(record);
  }

  renderTable(data); // this will now work if renderTable expects an array
}



async function loadServerData() {
  const req = await fetch(`${API_BASE_URL}/admin/systems/`);
  const response = await req.json();
  console.log(response);
  renderTable(response); // Pass the parsed data to renderTable
 
}

// Renders table rows using the provided data
async function renderTable(data) {
  const tbody = document.querySelector('#dataTable tbody'); // Moved here
  tbody.innerHTML = ''; // Clear existing rows
  console.log(data);
  // Store in global `records` and map in the sysid
  records = Object.entries(data).map(([sysid, obj]) => ({
    sysid,
    ...obj
  }));

  records.forEach((rec, index) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${index + 1}</td>
      ${p(index, "Sysname", rec["sysname"])}
      ${p(index, "NAC", rec["nac"])}
      <td class="text-center">
        <i class="fas fa-trash-alt text-danger mr-4" role="button" onclick="deleteRow(${index})"></i>
        <i class="fa fa-pencil text-primary" role="button" onclick="editRecord(${index})"></i>
        </i>
      </td>
    `;
    tbody.appendChild(row);
  });
}


  function createTableInputField(index, field, value) {
    const safeValue = String(value ?? '').replace(/"/g, '&quot;');
    return `
      <td>
        <input class="form-control form-control-sm"
               value="${safeValue}"
               title="${field}"
               onchange="updateField(${index}, '${field}', this.value)">
      </td>
    `;
  }

  function p(index, id, text){
    return `<td id="${id}" data-index="${index}" class="text-truncate">${text}</td>`;
  }
  function createTableHiddenField(innerHTML, fieldName, fieldValue) {
    return `<td>
  ${innerHTML}<input type="hidden" name="${fieldName}" value="${value}">
    </td>
    `

  }
  
function deleteRow(index) {
  if (confirm("Are you sure you want to delete this row?")) {
    records.splice(index, 1);
    renderTable();
  }
}

function updateField(index, field, value) {
  if (!records[index]) records[index] = {};
  records[index][field] = value;
}

function addRow() {
  const newRow = {};
  shownFields.forEach(field => newRow[field] = '');
  records.push(newRow);
  renderTable();
}



