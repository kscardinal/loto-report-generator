// input_form.js

let sourceCount = 0;
const MAX_SOURCES = 8;

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

// Utility to get input value by ID
function getVal(id) {
    const el = document.getElementById(id);
    if (!el) return "";
    let val = el.value.trim();

    // Default dates to today if empty
    if ((id === "date" || id === "completedDate") && val === "") {
        val = formatDateToMDY(new Date());
    }
    return val;
}

// Format date to MM/DD/YYYY
function formatDateToMDY(date) {
    const mm = String(date.getMonth() + 1).padStart(2, "0");
    const dd = String(date.getDate()).padStart(2, "0");
    const yyyy = date.getFullYear();
    return `${mm}/${dd}/${yyyy}`;
}

// Get just the filename from file input
function getFileName(input) {
    if (input.files && input.files.length > 0) {
        return input.files[0].name;
    }
    return "";
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
        <label>Energy Source: <input type="text" class="energy_source" /></label>
        <label>Chemical Name: <input type="text" class="chemical_name" /></label>
        <label>Volt: <input type="text" class="volt" /></label>
        <label>PSI: <input type="text" class="psi" /></label>
        <label>LBS: <input type="text" class="lbs" /></label>
        <label>Temp: <input type="text" class="temp" /></label>
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

    // Check if any inputs have value
    const inputs = lastSource.querySelectorAll("input");
    let hasText = false;
    inputs.forEach(input => {
        if (input.type === "file") {
            if (getFileName(input) !== "") hasText = true;
        } else if (input.value.trim() !== "") {
            hasText = true;
        }
    });

    if (hasText) {
        if (!confirm("The last source contains data. Are you sure you want to remove it?")) {
            return;
        }
    }

    lastSource.remove();
    sourceCount--;
}

// Gather form data
function gatherData() {
    const obj = {};

    // Add general fields
    for (const id in fieldMap) {
        const key = fieldMap[id];
        if (key) {
            const val = getVal(id);
            if (val !== "") {
                obj[key] = val;
            }
        }
    }

    // Add sources if they have data
    const sourceDivs = document.querySelectorAll(".source");
    const sources = [];

    sourceDivs.forEach(div => {
        const s = {};
        div.querySelectorAll("input").forEach(input => {
            let val = "";
            if (input.type === "file") {
                val = getFileName(input);
            } else {
                val = input.value.trim();
            }
            if (input.className && val !== "") {
                s[input.className] = val;
            }
        });
        if (Object.keys(s).length > 0) {
            sources.push(s);
        }
    });

    if (sources.length > 0) {
        obj.sources = sources;
    }

    return obj;
}

// Generate JSON and show in textarea
function generateJSON() {
    const obj = gatherData();
    const output = document.getElementById("output");
    if (output) output.value = JSON.stringify(obj, null, 2);
}

// Download JSON file
function downloadOutput() {
    const output = document.getElementById("output");
    const content = output?.value;
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

// Attach listeners after DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("addSourceBtn")?.addEventListener("click", addSource);
    document.getElementById("removeSourceBtn")?.addEventListener("click", removeLastSource);
    document.getElementById("generateBtn")?.addEventListener("click", generateJSON);
    document.getElementById("downloadBtn")?.addEventListener("click", downloadOutput);
});
