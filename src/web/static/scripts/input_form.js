// src/web/scripts/input_form.ts
var _a, _b, _c, _d;
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
// Utility to get input value by ID
function getVal(id) {
    var _a;
    return ((_a = document.getElementById(id)) === null || _a === void 0 ? void 0 : _a.value.trim()) || "";
}
// Add a new source
export function addSource() {
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
        <label>Isolation Point: <input type="text" class="isolation_point" /></label>
        <label>Isolation Method: <input type="text" class="isolation_method" /></label>
        <label>Verification Method: <input type="text" class="verification_method" /></label>
        <label>Verification Device: <input type="text" class="verification_device" /></label>
    `;
    container === null || container === void 0 ? void 0 : container.appendChild(div);
    sourceCount++;
}
// Remove the last source
export function removeLastSource() {
    if (sourceCount === 0)
        return;
    const container = document.getElementById("sources");
    const lastSource = container === null || container === void 0 ? void 0 : container.lastElementChild;
    if (!lastSource)
        return;
    const inputs = lastSource.querySelectorAll("input");
    let hasText = false;
    inputs.forEach(input => {
        if (input.value.trim() !== "") {
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
export function gatherData() {
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
            const cls = input.className;
            const val = input.value.trim();
            if (cls && val !== "") {
                s[cls] = val;
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
export function generateJSON() {
    const obj = gatherData();
    const output = document.getElementById("output");
    if (output)
        output.value = JSON.stringify(obj, null, 2);
}
// Download JSON file
export function downloadOutput() {
    const output = document.getElementById("output");
    const content = output === null || output === void 0 ? void 0 : output.value;
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
// Attach to buttons
(_a = document.getElementById("addSourceBtn")) === null || _a === void 0 ? void 0 : _a.addEventListener("click", addSource);
(_b = document.getElementById("removeSourceBtn")) === null || _b === void 0 ? void 0 : _b.addEventListener("click", removeLastSource);
(_c = document.getElementById("generateBtn")) === null || _c === void 0 ? void 0 : _c.addEventListener("click", generateJSON);
(_d = document.getElementById("downloadBtn")) === null || _d === void 0 ? void 0 : _d.addEventListener("click", downloadOutput);
//# sourceMappingURL=input_form.js.map