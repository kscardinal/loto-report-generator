console.log("input_form.js");

// ===============
// ACTION BUTTONS
// ===============

const downloadButton = document.getElementById("downloadBtn");
const generateButton = document.getElementById("generateBtn");
const uploadButton = document.getElementById("uploadBtn");

let fieldValidity = {};
let downloadable = false;

// === Utility: enable/disable a button based on downloadable ===
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

// === Utility: enable/disable source add/remove buttons ===
function updateSourceButton(buttonElement, numSources, maxSources) {
    if (buttonElement === removeSourceButton) {
        buttonElement.disabled = numSources <= 0;
        buttonElement.style.cursor = numSources > 0 ? "pointer" : "not-allowed";
        buttonElement.classList.toggle("button-disabled", numSources <= 0);
    } else if (buttonElement === addSourceButton) {
        buttonElement.disabled = numSources >= maxSources;
        buttonElement.style.cursor = numSources < maxSources ? "pointer" : "not-allowed";
        buttonElement.classList.toggle("button-disabled", numSources >= maxSources);
    } else {
        console.log("ERROR");
    }
}

// === Utility: update main buttons ===
function updateButtons() {
    updateButton(downloadButton);
    updateButton(generateButton);
    updateButton(uploadButton);
}

// === Utility: update source buttons ===
function updateSourceButtons() {
    updateSourceButton(addSourceButton, sourceCount, MAX_SOURCES);
    updateSourceButton(removeSourceButton, sourceCount, MAX_SOURCES);
}


// ===============
// VALIDATION HELPERS
// ===============

// === Tool: check if file is valid image ===
function isImageFile(file) {
    const validTypes = ["image/jpg", "image/jpeg", "image/png"];
    const validExt = /\.(jpg|jpeg|png)$/i;
    const match = file.name.toLowerCase().match(/\.([a-z0-9]+)$/);
    const extension = match ? match[1] : null;
    const isValid = validTypes.includes(file.type) && validExt.test(file.name);
    return { isValid, extension };
}


// ===============
// UNIFIED INPUT VALIDATION
// ===============

// === Tool: validate a specific input field ===
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

// === Initialize validation for static fields ===
validateInput({ id: "procedure_number", type: "number" });
validateInput({ id: "revision", type: "number" });
validateInput({ id: "origin", type: "number" });
validateInput({ id: "isolation_points", type: "number" });
validateInput({ id: "machine_image", type: "image" });
downloadable = Object.values(fieldValidity).every(Boolean);
updateButtons();


// ===============
// TODAY BUTTON
// ===============

// === Tool: set input to today ===
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

todayButton("date");
todayButton("completed_date");


// ===============
// SET TEXT VIA BUTTON
// ===============

// === Tool: set input text via button click ===
function setText(inputId, text) {
    const inputElement = document.getElementById(inputId);
    const buttonElement = document.getElementById(inputId + "_button");
    if (!inputElement || !buttonElement) return;

    buttonElement.addEventListener("click", () => {
        inputElement.value = text;
    });
}

setText("approved_by_company", "Cardinal Compliance Consultants");


// ===============
// IMAGE UTILS
// ===============

// === Tool: clear a photo input ===
function clearPhoto(inputId) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(inputId + "_preview");
    const label = document.getElementById(inputId + "_label");
    const button = document.getElementById(inputId + "_button");
    const picker = document.getElementById(inputId + "_picker");
    if (!input || !preview || !label || !button) return;

    input.value = "";
    preview.src = "";
    preview.style.display = "none";
    button.style.display = "none";
    label.style.display = "none";
    label.textContent = "";
    if (picker) picker.classList.remove("error");
    fieldValidity[inputId] = true;

    downloadable = Object.values(fieldValidity).every(Boolean);
    updateButtons();
}

// === Tool: setup image preview and clear button ===
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
            preview.style.display = "none";
            preview.src = "";
            button.style.display = "none";
            label.style.display = "none";
            if (picker) picker.classList.remove("error");
            fieldValidity[inputId] = true;
        } else if (!valid) {
            preview.style.display = "none";
            preview.src = "";
            button.style.display = "inline-block";
            label.style.display = "block";
            label.textContent = " ❌ File not supported. Only jpg, jpeg, png";
            if (picker) picker.classList.add("error");
            fieldValidity[inputId] = false;
        } else {
            preview.src = URL.createObjectURL(file);
            preview.style.display = "block";
            button.style.display = "inline-block";
            label.style.display = "none";
            if (picker) picker.classList.remove("error");
            fieldValidity[inputId] = true;

            preview.onload = () => URL.revokeObjectURL(preview.src);
        }

        downloadable = Object.values(fieldValidity).every(Boolean);
        updateButtons();
    });

    button.addEventListener("click", () => clearPhoto(inputId));
}

setupImagePreview("machine_image");


// ===============
// SOURCES
// ===============

const addSourceButton = document.getElementById("addSourceBtn");
const removeSourceButton = document.getElementById("removeSourceBtn");

addSourceButton.addEventListener("click", function() {
    addSource();
    updateSourceButtons();
});
removeSourceButton.addEventListener("click", function() {
    removeLastSource();
    updateSourceButtons();
});

let sourceCount = 0;
const MAX_SOURCES = 12;
updateSourceButtons();

let energyData = {};
const sourcesContainer = document.getElementById("sources");

// === Tool: load energy sources JSON ===
fetch("/static/dependencies/energySources.json")
    .then(res => res.ok ? res.json() : Promise.reject("Failed to load"))
    .then(data => { energyData = data; })
    .catch(err => console.error("Error loading energy sources:", err));


// === Tool: add a new source dynamically ===
function addSource() {
    if (sourceCount >= MAX_SOURCES) { alert(`Max ${MAX_SOURCES} sources allowed`); return; }

    const div = document.createElement("div");
    div.className = "source";
    div.dataset.index = sourceCount;

    const energyOptions = Object.keys(energyData).map(e => `<option value="${e}">${e}</option>`).join("");
    div.innerHTML = `
        <div class="source-header">Source ${sourceCount + 1}</div>
        <label>Energy Source: <select class="energy_source">${energyOptions}</select></label>
        <div class="dynamic-inputs"></div>
        <label>Device: <select class="device"></select></label>
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
        <label>Isolation Method: <select class="isolation_method"></select></label>
        <label>Verification Method: <select class="verification_method"></select></label>
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
    updateSourceDropdowns(div, energySelect.value);
    energySelect.addEventListener("change", () => updateSourceDropdowns(div, energySelect.value));

    validateInput({ id: `isolation_point_${sourceCount}`, type: "image" });
    validateInput({ id: `verification_device_${sourceCount}`, type: "image" });
    setupImagePreview(`verification_device_${sourceCount}`);
    setupImagePreview(`isolation_point_${sourceCount}`);

    sourceCount++;
}

// === Tool: remove last source ===
function removeLastSource() {
    if (sourceCount === 0) return;
    const lastSource = sourcesContainer.lastElementChild;
    const inputs = lastSource.querySelectorAll("input");
    let hasText = Array.from(inputs).some(input => input.value.trim() !== "");
    if (hasText && !confirm("The last source contains data. Remove anyway?")) return;

    inputs.forEach(input => { delete fieldValidity[input.id]; });
    lastSource.remove();
    sourceCount--;
    downloadable = Object.values(fieldValidity).every(Boolean);
    updateButtons();
}

// === Tool: populate source dropdowns and dynamic fields ===
function updateSourceDropdowns(sourceDiv, energy) {
    const data = energyData[energy];
    const device = sourceDiv.querySelector(".device");
    const isolation = sourceDiv.querySelector(".isolation_method");
    const verification = sourceDiv.querySelector(".verification_method");
    const dynamicInputs = sourceDiv.querySelector(".dynamic-inputs");

    dynamicInputs.querySelectorAll("input").forEach(input => delete fieldValidity[input.id]);
    dynamicInputs.innerHTML = "";

    function populateDropdown(selectElem, items, name) {
        selectElem.innerHTML = items.map(d => `<option value="${d}">${d}</option>`).join("") + `<option value="__custom__">Other (custom)</option>`;
        let customInput = document.createElement("input");
        customInput.type = "text";
        customInput.className = `${name}_custom custom-input`;
        customInput.placeholder = `Enter custom ${name.replace("_"," ")}...`;
        customInput.style.display = "none";
        customInput.style.marginTop = "5px";
        customInput.style.width = "100%";
        selectElem.parentElement.appendChild(customInput);

        selectElem.addEventListener("change", () => {
            customInput.style.display = selectElem.value === "__custom__" ? "block" : "none";
            if (selectElem.value !== "__custom__") customInput.value = "";
        });
    }

    populateDropdown(device, data.device, "device");
    populateDropdown(isolation, data.isolation_method, "isolation_method");
    populateDropdown(verification, data.verification_method, "verification_method");

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
        const warning = document.createElement("p");
        warning.className = "warning_label";
        warning.id = inputId + "_label";

        label.appendChild(input);
        dynamicInputs.appendChild(label);
        dynamicInputs.appendChild(warning);

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

    downloadable = Object.values(fieldValidity).every(Boolean);
    updateButtons();
}
