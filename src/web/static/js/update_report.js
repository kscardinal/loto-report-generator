// Back Button
const backButton = document.getElementById("backBtn");
backButton.addEventListener("click", async function() {
    console.log("Clicked Back Button!");
});

// Update Button
const updateButton = document.getElementById("updateBtn");
updateButton.addEventListener("click", function() {
    console.log("Clicked Update Button!")
});

// Add Source Button
const addSourceButton = document.getElementById("addSourceBtn");
addSourceButton.addEventListener("click", function() {
    console.log("Clicked Add Source Button!");
});

async function loadData() {
    const response = await fetch(`/get_report_json/${reportName}`);
    if (!response.ok) throw new Error("Report not found");
    const data = await response.json();
    console.log(data);
    return data;
}

async function setName() {
    const reportName = document.getElementById("name");
    if (window.reportName) {
        reportName.value = window.reportName;
        reportName.disabled = true;
    } else {
        reportName.disabled = false;
    }
}

async function setData_text(elementID, data) {
    const element = document.getElementById(elementID);
    const element_value = data[elementID];
    if (!element_value) { return };
    element.value = element_value;
}

async function setSourceData_text(elementID, dataID, data) {
    const element = document.getElementById(elementID);
    const element_value = data[dataID];
    if (!element_value) { return };
    element.value = element_value;
}

async function setData_date(elementID, data) {
    const element = document.getElementById(elementID);
    const old_date = data[elementID];
    if (!old_date) { return } 
    const [month, day, year] = old_date.split('/');
    const new_date = `${year}-${month}-${day}`;
    element.value = new_date;
}

async function setData_photo(elementID, data) {
    const input_element = document.getElementById(elementID);
    const element = document.getElementById(elementID + "_preview");
    const image_name = data[elementID];
    if (!image_name) { return }

    const response = await fetch(`/photo_by_name/${image_name}`);
    if (!response.ok) {
        throw new Error('Failed to fetch image');
    }
    const blob = await response.blob();
    const imageUrl = URL.createObjectURL(blob);
    element.src = imageUrl;
    element.style.display = "inline";

    input_element.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            const imageUrl = URL.createObjectURL(file);
            element.src = imageUrl;
            element.style.display = "inline";
        } else {
            element.style.display = "none";
        }
    });
}

async function setSourceData_photo(elementID, dataID, data) {
    const input_element = document.getElementById(elementID);
    const element = document.getElementById(elementID + "_preview");
    const image_name = data[dataID];
    if (!image_name) { return }

    const response = await fetch(`/photo_by_name/${image_name}`);
    if (!response.ok) {
        throw new Error('Failed to fetch image');
    }
    const blob = await response.blob();
    const imageUrl = URL.createObjectURL(blob);
    element.src = imageUrl;
    element.style.display = "inline";

    input_element.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            const imageUrl = URL.createObjectURL(file);
            element.src = imageUrl;
            element.style.display = "inline";
        } else {
            element.style.display = "none";
        }
    });
}

async function setSourceData_dropdown(elementID, dataID, data, sourceNum) {
    const element = document.getElementById(elementID);
    const element_value = data[dataID];
    if (!element_value) { return };
    if (dataID === "energy_source") { 
      element.value = data["energy_source"];
      return
    }

    const custom = energyData[data["energy_source"]][dataID].includes(data[dataID]);

    if (!custom) {
      console.log("Custom value detected:", dataID, `(${sourceNum + 1})`, "=", data[dataID]);
      element.value = "__custom__";
    } else {
      element.value = element_value;
    }

}

async function setData_source(sourceNum, data) {
    const sourceElement = document.querySelector(`.source#source_${sourceNum + 1}`);
    const divElement = document.getElementById(`source_${sourceNum + 1}`)
    const dropdownIds = Array.from(sourceElement.querySelectorAll('select')).map(input => input.id);
    for (const id of dropdownIds) {
        setSourceData_dropdown(id, id.replace(/[^a-zA-Z_]/g, '').replace(/_+$/g, ''), data.sources[sourceNum], sourceNum);
        updateSourceDropdowns(divElement, data.sources[sourceNum]["energy_source"]);
        setSourceData_dropdown(id, id.replace(/[^a-zA-Z_]/g, '').replace(/_+$/g, ''), data.sources[sourceNum], sourceNum);
    }
    const textInputIds = Array.from(sourceElement.querySelectorAll('input[type="text"]')).map(input => input.id);
    for (const id of textInputIds) {
        setSourceData_text(id, id.replace(/[^a-zA-Z_]/g, '').replace(/_+$/g, ''), data.sources[sourceNum]);
    }
    const photoInputIds = Array.from(sourceElement.querySelectorAll('input[type="file"]')).map(input => input.id);
    for (const id of photoInputIds) {
        setSourceData_photo(id, id.replace(/[^a-zA-Z_]/g, '').replace(/_+$/g, ''), data.sources[sourceNum]);
    }
    document.getElementById(`source_${sourceNum + 1}`).style.display = "block";
}

document.addEventListener('DOMContentLoaded', async function() {
  try {
    activateDropdowns();
    setName();
    const data = await loadData();
    const textInputIds = Array.from(document.querySelectorAll('input[type="text"]')).map(input => input.id);
    for (const id of textInputIds) {
      setData_text(id, data);
    }
    const dateInputIds = Array.from(document.querySelectorAll('input[type="date"]')).map(input => input.id);
    for (const id of dateInputIds) {
      setData_date(id, data);
    }
    const photoInputIds = Array.from(document.querySelectorAll('input[type="file"]')).map(input => input.id);
    for (const id of photoInputIds) {
      setData_photo(id, data);
    }
    await Promise.all(
        data.sources.map((_, i) => setData_source(i, data))
    );
  } catch (error) {
    console.error('Error:', error);
  }
});

let MAX_SOURCES = 0;
let energyData = {};

async function activateDropdowns() {
    MAX_SOURCES = Math.max(
    ...Array.from(document.querySelectorAll('[id^="source_"]'))
        .map(el => parseInt(el.id.replace('source_', '')) || 0)
    );

    // Load data from JSON file
    fetch("/static/dependencies/energySources.json")
    .then(res => res.ok ? res.json() : Promise.reject("Failed to load"))
    .then(data => {
        energyData = data;
        populateAllSources();
    })
    .catch(err => console.error("Error loading energy sources:", err));
}

function populateAllSources() {
  for (let i = 1; i <= MAX_SOURCES; i++) {
    const sourceDiv = document.getElementById(`source_${i}`);
    if (!sourceDiv) continue;

    const energySelect = sourceDiv.querySelector(".energy_source");
    if (!energySelect) continue;

    // Populate energy_source dropdown options
    const energyOptions = Object.keys(energyData).map(e =>
      `<option value="${e}">${e}</option>`
    ).join("");
    energySelect.innerHTML = energyOptions;

    // Set initial selection and populate dependent dropdowns
    const initialEnergy = energySelect.value || Object.keys(energyData)[0];
    energySelect.value = initialEnergy;
    updateSourceDropdowns(sourceDiv, initialEnergy);

    // Update dependent dropdowns on energy source change
    energySelect.addEventListener("change", () => {
      updateSourceDropdowns(sourceDiv, energySelect.value);
    });
  }
}

function updateSourceDropdowns(sourceDiv, energy) {
  const data = energyData[energy];
  if (!data) return;

  const device = sourceDiv.querySelector(".device");
  const isolation = sourceDiv.querySelector(".isolation_method");
  const verification = sourceDiv.querySelector(".verification_method");
  const dynamicInputs = sourceDiv.querySelector(".dynamic-inputs");

  // Clear previous custom inputs and dynamic inputs
  sourceDiv.querySelectorAll(".custom-input").forEach(el => el.remove());
  dynamicInputs.innerHTML = "";

  function populateDropdown(selectElem, items, name) {
    selectElem.innerHTML = items.map(d =>
      `<option value="${d}">${d}</option>`).join("") +
      `<option value="__custom__">Other (custom)</option>`;

    // Add hidden custom input field next to dropdown
    const customInput = document.createElement("input");
    customInput.type = "text";
    customInput.className = `${name}_custom custom-input`;
    customInput.placeholder = `Enter custom ${name.replace("_", " ")}...`;
    customInput.style.display = "none";
    customInput.style.marginTop = "5px";
    customInput.style.width = "100%";
    selectElem.insertAdjacentElement("afterend", customInput);

    // Show custom input when "Other (custom)" selected
    selectElem.addEventListener("change", () => {
      if (selectElem.value === "__custom__") {
        customInput.style.display = "block";
      } else {
        customInput.style.display = "none";
        customInput.value = "";
      }
    });
  }

  populateDropdown(device, data.device, "device");
  populateDropdown(isolation, data.isolation_method, "isolation_method");
  populateDropdown(verification, data.verification_method, "verification_method");

  // Add dynamic text inputs as per data.inputs array
  data.inputs.forEach(inputObj => {
    const { field_name, unit_name, title_name } = inputObj;
    const inputId = `${field_name}_${sourceDiv.id.split('_')[1]}`;

    const label = document.createElement("label");
    label.textContent = title_name + ": ";
    const input = document.createElement("input");
    input.type = "text";
    input.id = inputId;
    input.placeholder = unit_name;
    input.style.width = "100%";
    const warning = document.createElement("p");
    warning.className = "warning_label";
    warning.id = inputId + "_label";

    label.appendChild(input);
    dynamicInputs.appendChild(label);
    dynamicInputs.appendChild(warning);
  });
}
