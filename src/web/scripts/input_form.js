// -----------------------------
// Action Buttons
// -----------------------------
const downloadButton = document.getElementById("downloadBtn");
const generateButton = document.getElementById("generateBtn");

let fieldValidity = {};
let downloadable = false;

function updateButton(buttonElement) {
    if (downloadable) {
        buttonElement.disabled = false;
        buttonElement.style.cursor = "pointer";
        buttonElement.classList.remove("button-disabled");
    } else {
        buttonElement.disabled = true;
        buttonElement.style.cursor = "not-allowed";
        buttonElement.classList.add("button-disabled");
    }
}

function updateSourceButton(buttonElement, numSources, maxSources) {
    if (buttonElement === removeSourceButton) {
        if (numSources > 0) {
            buttonElement.disabled = false;
            buttonElement.style.cursor = "pointer";
            buttonElement.classList.remove("button-disabled");       
         } else {
            buttonElement.disabled = true;
            buttonElement.style.cursor = "not-allowed";
            buttonElement.classList.add("button-disabled");
        }
    } else if (buttonElement === addSourceButton) {
        if (numSources === maxSources) {
            buttonElement.disabled = true;
            buttonElement.style.cursor = "not-allowed";
            buttonElement.classList.add("button-disabled");
        } else {
            buttonElement.disabled = false;
            buttonElement.style.cursor = "pointer";
            buttonElement.classList.remove("button-disabled");
        }
    } else {
        console.log("ERROR");
    }


}

function updateButtons() {
    updateButton(downloadButton);
    updateButton(generateButton);
}

function updateSourceButtons() {
    updateSourceButton(addSourceButton, sourceCount, MAX_SOURCES);
    updateSourceButton(removeSourceButton, sourceCount, MAX_SOURCES);
}


// -----------------------------
// Validation Helpers
// -----------------------------
function isImageFile(file) {
    const validTypes = ["image/jpg", "image/jpeg", "image/png"];
    const validExt = /\.(jpg|jpeg|png)$/i;
    const match = file.name.toLowerCase().match(/\.([a-z0-9]+)$/);
    const extension = match ? match[1] : null;
    const isValid = validTypes.includes(file.type) && validExt.test(file.name);
    return { isValid, extension };
}


// -----------------------------
// Unified Input Validation
// -----------------------------
function validateInput({ id, type }) {
    const input = document.getElementById(id);
    const label = document.getElementById(id + "_label");
    if (!input || !label) return;

    fieldValidity[id] = true;

    if (type === "number") {
        input.addEventListener("input", () => {
            const val = input.value;
            const isValid = val.length === 0 || /^\d+$/.test(val);

            if (!isValid) {
                label.style.display = "block";
                label.textContent = " ❌ Must only be a number";
                input.classList.add("error");
            } else {
                label.style.display = "none";
                input.classList.remove("error");
            }

            fieldValidity[id] = isValid;
            downloadable = Object.values(fieldValidity).every(Boolean);
            updateButtons();
        });
    } else if (type === "image") {
        const picker = document.getElementById(id + "_picker");
        const preview = document.getElementById(id + "_preview");
        const button = document.getElementById(id + "_button");
        if (!picker || !preview) return;

        input.addEventListener("change", () => {
            const file = input.files[0];
            const { isValid, extension } = file ? isImageFile(file) : { isValid: true };

            if (!file) {
                label.style.display = "none";
                picker.classList.remove("error");
                preview.style.display = "none";
                fieldValidity[id] = true;
                button.style.display = "none";
            } else if (!isValid) {
                label.style.display = "block";
                label.textContent = ` ❌ ${extension || "File"} not supported. Only jpg, jpeg, png`;
                picker.classList.add("error");
                preview.style.display = "none";
                fieldValidity[id] = false;
                button.style.display = "block";
            } else {
                label.style.display = "none";
                picker.classList.remove("error");
                preview.src = URL.createObjectURL(file);
                preview.style.display = "block";
                preview.onload = () => URL.revokeObjectURL(preview.src);
                fieldValidity[id] = true;
                button.style.display = "block";
            }

            downloadable = Object.values(fieldValidity).every(Boolean);
            updateButtons();
        });
    }
}


// -----------------------------
// Initialize Validation for static fields
// -----------------------------
validateInput({ id: "procedure_number", type: "number" });
validateInput({ id: "revision", type: "number" });
validateInput({ id: "origin", type: "number" });
validateInput({ id: "isolation_points", type: "number" });
validateInput({ id: "machine_image", type: "image" });

// Initial check for buttons
downloadable = Object.values(fieldValidity).every(Boolean);
updateButtons();

// -----------------------------
// Today Button Setup
// -----------------------------
function todayButton(inputId) {
    const inputElement = document.getElementById(inputId);
    const buttonElement = document.getElementById(inputId + "_button");
    if (!inputElement || !buttonElement) return;

    buttonElement.addEventListener("click", () => {
        const today = new Date();
        const yyyy = today.getFullYear();
        const mm = String(today.getMonth() + 1).padStart(2, "0");
        const dd = String(today.getDate()).padStart(2, "0");
        inputElement.value = `${yyyy}-${mm}-${dd}`;
    });
}

// Initialize Today buttons
todayButton("date");
todayButton("completed_date");


// -----------------------------
// Set Text via Button
// -----------------------------
function setText(inputId, text) {
    const inputElement = document.getElementById(inputId);
    const buttonElement = document.getElementById(inputId + "_button");
    if (!inputElement || !buttonElement) return;

    buttonElement.addEventListener("click", () => {
        inputElement.value = text;
    });
}

// Example: automatically set Approved By Company
setText("approved_by_company", "Cardinal Compliance Consultants");


function clearPhoto(inputId) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(inputId + "_preview");
    const label = document.getElementById(inputId + "_label");
    const button = document.getElementById(inputId + "_button"); // ← get the clear button
    const picker = document.getElementById(inputId + "_picker");

    if (!input || !preview || !label || !button) return;

    // Clear the file input
    input.value = "";

    // Hide the preview
    preview.src = "";
    preview.style.display = "none";

    // Hide the clear button
    button.style.display = "none";

    // Reset warning label
    label.style.display = "none";
    label.textContent = "";

    // Remove error highlight
    if (picker) picker.classList.remove("error");

    // Reset field validity
    fieldValidity[inputId] = true;

    // Recalculate downloadable and update buttons
    downloadable = Object.values(fieldValidity).every(Boolean);
    updateButtons();
}


// -----------------------------
// Setup image preview for a file input
// -----------------------------
function setupImagePreview(inputId) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(inputId + "_preview");
    const button = document.getElementById(inputId + "_button");
    const label = document.getElementById(inputId + "_label");
    const picker = document.getElementById(inputId + "_picker");

    if (!input || !preview || !button || !label) return;

    input.addEventListener("change", () => {
        const file = input.files[0];
        const valid = file ? file.type.startsWith("image/") && /\.(jpg|jpeg|png)$/i.test(file.name) : false;

        if (!file) {
            // No file selected: hide preview, hide button
            preview.style.display = "none";
            preview.src = "";
            button.style.display = "none";
            label.style.display = "none";
            if (picker) picker.classList.remove("error");
            fieldValidity[inputId] = true;
        } else if (!valid) {
            // Invalid file: hide preview but show clear button
            preview.style.display = "none";
            preview.src = "";
            button.style.display = "inline-block";
            label.style.display = "block";
            label.textContent = " ❌ File not supported. Only jpg, jpeg, png";
            if (picker) picker.classList.add("error");
            fieldValidity[inputId] = false;
        } else {
            // Valid file: show preview and clear button
            preview.src = URL.createObjectURL(file);
            preview.style.display = "block";
            button.style.display = "inline-block";
            label.style.display = "none";
            if (picker) picker.classList.remove("error");
            fieldValidity[inputId] = true;

            preview.onload = () => URL.revokeObjectURL(preview.src); // free memory
        }

        downloadable = Object.values(fieldValidity).every(Boolean);
        updateButtons();
    });

    // Always attach clear button
    button.addEventListener("click", () => clearPhoto(inputId));
}

// Initialize for your static field
setupImagePreview("machine_image");




// -----------------------------
// SOURCES ------------------
// -----------------------------

const  addSourceButton = document.getElementById("addSourceBtn");
const removeSourceButton = document.getElementById("removeSourceBtn");

addSourceButton.addEventListener("click", function() {
    addSource()
    updateSourceButtons()
});
removeSourceButton.addEventListener("click", function() {
    removeLastSource()
    updateSourceButtons()
});

// -----------------------------
// Sources Dynamic Section
// -----------------------------
let sourceCount = 0;
const MAX_SOURCES = 12; // adjust as needed
updateSourceButtons()

let energyData = {}; // placeholder

// Load energySources.json
fetch("dependencies/energySources.json")
    .then(response => {
        if (!response.ok) throw new Error("Failed to load energySources.json");
        return response.json();
    })
    .then(data => {
        energyData = data;

        // Optionally: initialize the first source if needed
        // addSource(); // if you want to auto-add a source on page load
    })
    .catch(err => {
        console.error("Error loading energy sources:", err);
    });


// Container for sources
const sourcesContainer = document.getElementById("sources");

// -----------------------------
// Add Source Function
// -----------------------------
function addSource() {
    if (sourceCount >= MAX_SOURCES) {
        alert(`Max ${MAX_SOURCES} sources allowed`);
        return;
    }

    const div = document.createElement("div");
    div.className = "source";
    div.dataset.index = sourceCount;

    const energyOptions = Object.keys(energyData)
        .map(e => `<option value="${e}">${e}</option>`)
        .join("");

    div.innerHTML = `
        <div class="source-header">Source ${sourceCount + 1}</div>
        <label>Energy Source:
            <select class="energy_source">${energyOptions}</select>
        </label>
        <div class="dynamic-inputs"></div>
        <label>Device:
            <select class="device"></select>
        </label>
        <label>Tag: <input type="text" id="tag" placeholder="0001" /></label>
        <label>Description: <input type="text" id="source_description" /></label>
        <label>Isolation Point: </label>
        <div class="input-with-preview" id="isolation_point_${sourceCount}_picker">
            <div class="inline-button-wrapper">
                <input type="file" accept="image/*" id="isolation_point_${sourceCount}" class="image-picker" />
                <button type="button" id="isolation_point_${sourceCount}_button" class="clear-photo-button">Clear</button>
            </div>
            <img id="isolation_point_${sourceCount}_preview" class="preview_image" />
        </div>
        <p class="warning_label" id="isolation_point_${sourceCount}_label"></p>
        <label>Isolation Method:
            <select class="isolation_method"></select>
        </label>
        <label>Verification Method:
            <select class="verification_method"></select>
        </label>
        <label>Verification Device: </label>
        <div class="input-with-preview" id="verification_device_${sourceCount}_picker">
            <div class="inline-button-wrapper">
                <input type="file" accept="image/*" id="verification_device_${sourceCount}" class="image-picker" />
                <button type="button" id="verification_device_${sourceCount}_button" class="clear-photo-button">Clear</button>
            </div>
            <img id="verification_device_${sourceCount}_preview" class="preview_image" />
        </div>
        <p class="warning_label" id="verification_device_${sourceCount}_label"></p>
    `;

    sourcesContainer.appendChild(div);

    const energySelect = div.querySelector(".energy_source");

    // Populate dependent dropdowns initially
    updateSourceDropdowns(div, energySelect.value);

    // Update dropdowns on energy source change
    energySelect.addEventListener("change", () => updateSourceDropdowns(div, energySelect.value));

    // Validate images and handle previews
    validateInput({ id: `isolation_point_${sourceCount}`, type: "image" });
    validateInput({ id: `verification_device_${sourceCount}`, type: "image" });

    // Setup image previews after they exist in DOM
    setupImagePreview(`verification_device_${sourceCount}`);
    setupImagePreview(`isolation_point_${sourceCount}`);

    sourceCount++;
}


// -----------------------------
// Remove Last Source Function
// -----------------------------
function removeLastSource() {
    if (sourceCount === 0) return;
    const lastSource = sourcesContainer.lastElementChild;

    // Check if there is any data
    const inputs = lastSource.querySelectorAll("input");
    let hasText = false;
    inputs.forEach(input => {
        if (input.value.trim() !== "") hasText = true;
    });
    if (hasText && !confirm("The last source contains data. Remove anyway?")) return;

    // Remove fieldValidity entries for this source
    inputs.forEach(input => {
        const id = input.id;
        if (fieldValidity.hasOwnProperty(id)) {
            delete fieldValidity[id];
        }
    });

    lastSource.remove();
    sourceCount--;

    // Recalculate downloadable
    downloadable = Object.values(fieldValidity).every(Boolean);
    updateButtons();
}



function updateSourceDropdowns(sourceDiv, energy) {
    const data = energyData[energy];
    const device = sourceDiv.querySelector(".device");
    const isolation = sourceDiv.querySelector(".isolation_method");
    const verification = sourceDiv.querySelector(".verification_method");
    const dynamicInputs = sourceDiv.querySelector(".dynamic-inputs");

    // Remove old dynamic inputs from fieldValidity
    const oldInputs = dynamicInputs.querySelectorAll("input");
    oldInputs.forEach(input => delete fieldValidity[input.id]);

    // Clear previous dynamic inputs
    dynamicInputs.innerHTML = "";

    // Helper: populate dropdown + add custom field support
    function populateDropdown(selectElem, items, name) {
        selectElem.innerHTML =
            items.map(d => `<option value="${d}">${d}</option>`).join("") +
            `<option value="__custom__">Other (custom)</option>`;

        // Create hidden input for custom text
        let customInput = document.createElement("input");
        customInput.type = "text";
        customInput.className = `${name}_custom custom-input`;
        customInput.placeholder = `Enter custom ${name.replace("_", " ")}...`;
        customInput.style.display = "none";
        customInput.style.marginTop = "5px";
        customInput.style.width = "100%";

        // Insert after the dropdown
        selectElem.parentElement.appendChild(customInput);

        // Handle selection changes
        selectElem.addEventListener("change", () => {
            if (selectElem.value === "__custom__") {
                customInput.style.display = "block";
            } else {
                customInput.style.display = "none";
                customInput.value = "";
            }
        });
    }

    // Populate dropdowns with “Other (custom)” support
    populateDropdown(device, data.device, "device");
    populateDropdown(isolation, data.isolation_method, "isolation_method");
    populateDropdown(verification, data.verification_method, "verification_method");

    // Create new inputs from array of objects
    data.inputs.forEach(inputObj => {
        const { field_name, unit_name, title_name } = inputObj;
        const inputId = `${field_name}_${sourceDiv.dataset.index}`;

        const label = document.createElement("label");
        label.textContent = title_name + ": ";

        const input = document.createElement("input");
        input.type = "text";
        input.id = inputId;
        input.placeholder = unit_name;
        input.style.width = "100%";

        // Add warning label
        const warning = document.createElement("p");
        warning.className = "warning_label";
        warning.id = inputId + "_label";

        label.appendChild(input);
        dynamicInputs.appendChild(label);
        dynamicInputs.appendChild(warning);

        // Setup validation: skip chemical_name
        fieldValidity[inputId] = true;
        input.addEventListener("input", () => {
            if (field_name === "chemical_name") {
                warning.style.display = "none";
                input.classList.remove("error");
                fieldValidity[inputId] = true;
            } else {
                const val = input.value;
                const isValid = val.length === 0 || /^\d+$/.test(val);
                if (!isValid) {
                    warning.style.display = "block";
                    warning.textContent = " ❌ Must only be a number";
                    input.classList.add("error");
                } else {
                    warning.style.display = "none";
                    input.classList.remove("error");
                }
                fieldValidity[inputId] = isValid;
            }
            downloadable = Object.values(fieldValidity).every(Boolean);
            updateButtons();
        });
    });

    // Recalculate downloadable
    downloadable = Object.values(fieldValidity).every(Boolean);
    updateButtons();
}
