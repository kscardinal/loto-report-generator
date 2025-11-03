let jsonData = null; // originally loaded JSON data
const updatedFields = {}; // to store changed fields

window.addEventListener("DOMContentLoaded", async () => {
    // Load report JSON first
    jsonData = await loadReportData();

    // Specify fields to track
    const fieldsToTrack = Object.keys(jsonData);
    fieldsToTrack.forEach(field => checkDifference(field));
});

async function loadReportData() {
    try {
        const res = await fetch(`/get_report_json/${window.reportName}`);
        if (!res.ok) throw new Error(`Failed to fetch report JSON: ${res.statusText}`);
        return await res.json();
    } catch (err) {
        console.error(err);
    }
}

function checkDifference(inputID) {
    const element = document.getElementById(inputID);
    if (!element || !jsonData) return;

    // Store the original value for comparison
    const originalValue = jsonData[inputID];

    // Add an event listener for real-time detection of changes
    element.addEventListener("change", () => {
        if (inputID.toLowerCase().includes("date")) {
            const [year, month, day] = element.value.split("-");
            const new_date = month + "/" + day + "/" + year;
            if (new_date !== originalValue) {
                // Store the change
                updatedFields[inputID] = new_date;
                element.classList.add("updated");
            } else {
                // Remove the field if reverted to original
                if (updatedFields.hasOwnProperty(inputID)) {
                    delete updatedFields[inputID];
                    element.classList.remove("updated");
                }
            }
        } else {
            if (element.value !== originalValue) {
                // Store the change
                updatedFields[inputID] = element.value;
                element.classList.add("updated");
            } else {
                // Remove the field if reverted to original
                if (updatedFields.hasOwnProperty(inputID)) {
                    delete updatedFields[inputID];
                    element.classList.remove("updated");
                }
            }
        }
        console.log("Tracked changes:", updatedFields);
    });
}


const updateButton = document.getElementById("updateBtn");

updateButton.addEventListener("click", async () => {
    if (!window.reportName || !updatedFields || Object.keys(updatedFields).length === 0) {
        console.log("No changes to update.");
        return;
    }

    // Convert updatedFields object to an array of {field, value} objects
    const updatesArray = Object.entries(updatedFields).map(([field, value]) => ({
        field,
        value
    }));

    try {
        const res = await fetch("/update_report_json", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                report_name: window.reportName,
                updates: updatesArray
            })
        });

        const data = await res.json();
        console.log("Update response:", data);

        if (res.ok) {
            // Optionally clear tracked changes after successful update
            Object.keys(updatedFields).forEach(k => delete updatedFields[k]);
        }

    } catch (err) {
        console.error("Failed to update report:", err);
    }

    window.location.href = "/update/" + window.reportName;
});


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
        inputElement.dispatchEvent(new Event('change'));
    });
}

todayButton("date");
todayButton("completed_date");

let fieldValidity = {};
let updatable = false;

let sourceCount = 0;
const MAX_SOURCES = 12;

// === Utility: enable/disable a button based on updatable ===
function updateButton_1(buttonElement) {
    if (updatable) {
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
    updateButton_1(updateButton);
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
            updatable = Object.values(fieldValidity).every(Boolean);
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
            updatable = Object.values(fieldValidity).every(Boolean);
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
updatable = Object.values(fieldValidity).every(Boolean);
updateButtons();

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

    updatable = Object.values(fieldValidity).every(Boolean);
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

        updatable = Object.values(fieldValidity).every(Boolean);
        updateButtons();
    });

    button.addEventListener("click", () => clearPhoto(inputId));
}

setupImagePreview("machine_image");


const renameButton = document.getElementById("renameBtn");
const nameField = document.getElementById("name");

renameButton.addEventListener("click", async () => {
    if (renameButton.textContent.toLowerCase() === "rename") {
        renameButton.textContent = "Cancel";
        nameField.disabled = false;
    } else {
        renameButton.textContent = "Rename";
        nameField.disabled = true;

        const newName = document.getElementById("name").value.trim();

        if (!newName) {
            alert("Please enter a new report name.");
            return;
        }

        if (newName === window.reportName) {
            return
        }

        try {
            const res = await fetch("/rename_report", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    old_name: window.reportName, // this is the current report
                    new_name: newName
                })
            });

            const data = await res.json();
            console.log("Rename response:", data);

            if (res.ok) {
                window.location.href = "/update/" + newName
            } else {
                alert(`Error: ${data.detail || "Rename failed"}`);
            }

        } catch (err) {
            console.error("Rename error:", err);
        }

    }
});

nameField.addEventListener("change", async function() {
    if (nameField.value !== window.reportName) {
        nameField.classList.add("updated");
        renameButton.textContent = "Save";
    } else {
        nameField.classList.remove("updated");
        renameButton.textContent = "Cancel";
    }
})