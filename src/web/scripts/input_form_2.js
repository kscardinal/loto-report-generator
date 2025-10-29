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

function updateButtons() {
    updateButton(downloadButton);
    updateButton(generateButton);
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
// Streamlined Input Validation
// -----------------------------
function inputValidation(fields) {
    fields.forEach(({ id, type }) => {
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
            input.addEventListener("change", () => {
                const file = input.files[0];
                if (!file) {
                    label.style.display = "none";
                    input.classList.remove("error");
                    fieldValidity[id] = true;
                    downloadable = Object.values(fieldValidity).every(Boolean);
                    updateButtons();
                    return;
                };
                const { isValid, extension } = isImageFile(file);
                if (!isValid) {
                    label.style.display = "block";
                    label.textContent = ` ❌ ${extension || "File"} not supported. Only jpg, jpeg, png`;
                    input.classList.add("error");
                } else {
                    label.style.display = "none";
                    input.classList.remove("error");
                }
                fieldValidity[id] = isValid;
                downloadable = Object.values(fieldValidity).every(Boolean);
                updateButtons();
            });
        }
    });
}

// -----------------------------
// Initialize Validation
// -----------------------------
inputValidation([
    { id: "procedure_number", type: "number" },
    { id: "revision", type: "number" },
    { id: "origin", type: "number" },
    { id: "isolation_points", type: "number" },
    { id: "machine_image", type: "image" }
]);

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
