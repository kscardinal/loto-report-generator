// src/web/scripts/input_form.js

const MAX_SOURCES = 8;
let sourceCount = 0;

// Map form IDs to JSON keys
const fieldMap = {
    name: "name",
    description: "description",
    procedureNumber: "procedure_number",
    facility: "facility",
    location: "location",
    revision: "revision",
    date: "date",
    origin: "origin",
    machineImage: "machine_image",
    isolationPoints: "isolation_points",
    notes: "notes",
    approvedBy: "approved_by",
    preparedBy: "prepared_by",
    approvedByCompany: "approved_by_company",
    completedDate: "completed_date"
};

// Energy source options and field mapping
const energyFields = {
    Electric: ["volt"],
    "Natural gas": ["psi"],
    Steam: ["psi"],
    Chemical: ["psi", "chemical_name"],
    Hydraulic: ["psi"],
    Gravity: ["lbs"],
    Thermal: ["temp"],
    Refrigerant: ["psi"],
    Water: ["psi"],
    Pneumatic: ["psi"]
};

// Utility to get input value by ID
function getVal(id) {
    const el = document.getElementById(id);
    return el ? el.value.trim() : "";
}

// Helper to get file input name
function getFileName(input) {
    return input.files && input.files[0] ? input.files[0].name : "";
}

// Add a new source
function addSource() {
    if (sourceCount >= MAX_SOURCES) {
        alert(`Max ${MAX_SOURCES} sources allowed`);
        return;
    }

    const container = document.getElementById("sources");
    const div = document.createElement("div");
    div.className = "source";

    div.innerHTML = `
        <div class="source-header">Source ${sourceCount + 1}</div>
        <label>Energy Source: 
            <select class="energy_source">
                <option value="">Select</option>
                <option value="Thermal">Thermal</option>
                <option value="Natural gas">Natural gas</option>
                <option value="Steam">Steam</option>
                <option value="Chemical">Chemical</option>
                <option value="Hydraulic">Hydraulic</option>
                <option value="Gravity">Gravity</option>
                <option value="Electric">Electric</option>
                <option value="Refrigerant">Refrigerant</option>
                <option value="Water">Water</option>
                <option value="Pneumatic">Pneumatic</option>
            </select>
        </label>
        <label>Chemical Name: <input type="text" class="chemical_name" /></label>
        <label>Volt: <input type="number" class="volt" /></label>
        <label>PSI: <input type="number" class="psi" /></label>
        <label>LBS: <input type="number" class="lbs" /></label>
        <label>Temp: <input type="number" class="temp" /></label>
        <label>Device: <input type="text" class="device" /></label>
        <label>Tag: <input type="text" class="tag" /></label>
        <label>Description: <input type="text" class="source_description" /></label>
        <label>Isolation Point: <input type="file" accept="image/*" class="isolation_point" /></label>
        <label>Isolation Method: <input type="text" class="isolation_method" /></label>
        <label>Verification Method: <input type="text" class="verification_method" /></label>
        <label>Verification Device: <input type="file" accept="image/*" class="verification_device" /></label>
    `;
    container.appendChild(div);
    sourceCount++;
}

// Remove the last source
function removeLastSource() {
    if (sourceCount === 0) return;

    const container = document.getElementById("sources");
    const lastSource = container.lastElementChild;
    if (!lastSource) return;

    const inputs = lastSource.querySelectorAll("input, select");
    let hasText = false;

    inputs.forEach(input => {
        if (input.type === "file") {
            if (input.files && input.files.length > 0) hasText = true;
        } else if (input.value.trim() !== "") {
            hasText = true;
        }
    });

    if (hasText && !confirm("The last source contains data. Are you sure you want to remove it?")) {
        return;
    }

    lastSource.remove();
    sourceCount--;
}

// Gather form data
function gatherData() {
    const obj = {};

    const today = new Date().toISOString().split("T")[0];

    // Add general fields
    for (const id in fieldMap) {
        const key = fieldMap[id];
        if (!key) continue;
        let val = getVal(id);
        if ((id === "date" || id === "completedDate") && val === "") {
            val = today;
        }
        if (val !== "") obj[key] = val;
    }

    // Validate numeric fields
    ["procedureNumber", "revision", "origin"].forEach(id => {
        const val = getVal(id);
        if (val && isNaN(Number(val))) {
            alert(`${id} must be a number`);
        }
    });

    // Add sources if they have data
    const sourceDivs = document.querySelectorAll(".source");
    const sources = [];

    sourceDivs.forEach(div => {
        const s = {};
        const inputs = div.querySelectorAll("input, select");
        inputs.forEach(input => {
            let val = "";
            if (input.tagName === "SELECT") {
                val = input.value;
            } else if (input.type === "file") {
                val = getFileName(input);
            } else {
                val = input.value.trim();
            }
            const cls = input.className;
            if (cls && val !== "") s[cls] = val;
        });
        if (Object.keys(s).length > 0) sources.push(s);
    });

    if (sources.length > 0) obj.sources = sources;

    return obj;
}

// Generate JSON
function generateJSON() {
    const obj = gatherData();
    const output = document.getElementById("output");
    if (output) output.value = JSON.stringify(obj, null, 2);
}

// Download JSON
function downloadOutput() {
    const output = document.getElementById("output");
    const content = output ? output.value : "";
    if (!content) {
        alert("Generate the JSON first!");
        return;
    }

    const filename = getVal("name") || "data";
    const blob = new Blob([content], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${filename}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

// Attach functions to window for global access
window.addSource = addSource;
window.removeLastSource = removeLastSource;
window.generateJSON = generateJSON;
window.downloadOutput = downloadOutput;

// Attach event listeners
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("addSourceBtn")?.addEventListener("click", addSource);
    document.getElementById("removeSourceBtn")?.addEventListener("click", removeLastSource);
    document.getElementById("generateBtn")?.addEventListener("click", generateJSON);
    document.getElementById("downloadBtn")?.addEventListener("click", downloadOutput);
});
