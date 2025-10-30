console.log("json_handlers.js");

// Module Stuff
const generateButton = document.getElementById("generateBtn");
const downloadButton = document.getElementById("downloadBtn");
let energyData = {};


// -----------------------------
// JSON Energy Data
// -----------------------------

// Load energySources.json
fetch("/static/dependencies/energySources.json")
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

// helpers ---------------------------------------------------------





function formatDate(value) {
    if (!value) return "";

    let parts;
    if (typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value)) {
        parts = value.split("-").map(Number);
        // year, month-1, day
        const d = new Date(parts[0], parts[1] - 1, parts[2]);
        const mm = String(d.getMonth() + 1).padStart(2, "0");
        const dd = String(d.getDate()).padStart(2, "0");
        const yyyy = d.getFullYear();
        return `${mm}/${dd}/${yyyy}`;
    } else {
        const d = new Date(value);
        if (isNaN(d)) return "";
        const mm = String(d.getMonth() + 1).padStart(2, "0");
        const dd = String(d.getDate()).padStart(2, "0");
        const yyyy = d.getFullYear();
        return `${mm}/${dd}/${yyyy}`;
    }
}


// return filename (not full path) or "" if none
function getFileName(input) {
    if (!input) return "";
    if (input.files && input.files.length > 0) {
        return input.files[0].name || "";
    }
    // if input.value holds a fakepath, extract filename fallback
    if (typeof input.value === "string" && input.value) {
        return input.value.split("\\").pop().split("/").pop();
    }
    return "";
}

// Add thousands separators for numeric strings (keeps non-numeric unchanged)
function formatNumberWithCommas(raw) {
    if (raw == null) return "";
    // remove commas, spaces
    const cleaned = String(raw).replace(/[, ]+/g, "").trim();
    // allow numeric with optional decimal (we treat integer case primarily)
    if (/^-?\d+(\.\d+)?$/.test(cleaned)) {
        const parts = cleaned.split(".");
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        return parts.join(".");
    }
    return String(raw); // not a pure number -> return original
}

// main ------------------------------------------------------------

export function generateJSON() {
    // static fields to collect (ids in DOM)
    const fields = [
        "description",
        "procedure_number",
        "facility",
        "location",
        "revision",
        "date",
        "origin",
        "machine_image",
        "isolation_points",
        "notes",
        "approved_by",
        "prepared_by",
        "approved_by_company",
        "completed_date"
    ];

    const jsonData = {};

    // gather static fields
    fields.forEach((id) => {
        const input = document.getElementById(id);
        if (!input) {
            jsonData[id] = "";
            return;
        }

        // Date handling
        if (input.type === "date") {
            jsonData[id] = formatDate(input.value);
            return;
        }

        // File handling
        if (input.type === "file") {
            jsonData[id] = getFileName(input);
            return;
        }

        // fallback for other inputs
        jsonData[id] = input.value || "";
    });

    // gather dynamic sources
    const sourceDivs = document.querySelectorAll(".source");
    const sources = [];

    sourceDivs.forEach((div) => {
        const idx = div.dataset.index;
        const sourceObj = {};

        // energy source
        const energySelect = div.querySelector(".energy_source");
        const energyVal = energySelect ? energySelect.value : "";
        if (!energyVal) return;

        sourceObj["energy_source"] = energyVal;

        // get data config
        const config = energyData[energyVal] || { inputs: [] };

        // Prepare values first
        let chemicalName = "";
        let unitValues = {};

        (config.inputs || []).forEach(inpObj => {
            const field = inpObj.field_name;
            const unit = inpObj.unit_name || "";
            const elIdIndexed = `${field}_${idx}`;
            const elIndexed = div.querySelector(`#${CSS.escape(elIdIndexed)}`);
            const elNonIndexed = div.querySelector(`#${CSS.escape(field)}`);
            const el = elIndexed || elNonIndexed;
            if (!el) return;

            const rawVal = el.value ? String(el.value).trim() : "";
            if (!rawVal) return;

            if (field === "chemical_name") {
                chemicalName = rawVal;
            } else {
                const formattedNumber = formatNumberWithCommas(rawVal);
                unitValues[field] = unit ? `${formattedNumber} ${unit}` : formattedNumber;
            }
        });

        // device (with custom)
        let deviceVal = "";
        const deviceEl = div.querySelector(".device");
        if (deviceEl && deviceEl.value) {
            if (deviceEl.value === "__custom__") {
                const customEl = div.querySelector(".device_custom");
                deviceVal = customEl ? customEl.value.trim() : "";
            } else {
                deviceVal = deviceEl.value;
            }
        }

        // tag
        let tagVal = "";
        const tagIndexed = div.querySelector(`#${CSS.escape(`tag_${idx}`)}`);
        const tagNon = div.querySelector(`#${CSS.escape(`tag`)}`);
        const tagEl = tagIndexed || tagNon;
        if (tagEl && tagEl.value.trim() !== "") tagVal = tagEl.value.trim();

        // description
        let descVal = "";
        const descIndexed = div.querySelector(`#${CSS.escape(`source_description_${idx}`)}`);
        const descNon = div.querySelector(`#${CSS.escape(`source_description`)}`);
        const descEl = descIndexed || descNon;
        if (descEl && descEl.value.trim() !== "") descVal = descEl.value.trim();

        // isolation point
        let isoPoint = "";
        const isolationInput = div.querySelector(`#${CSS.escape(`isolation_point_${idx}`)}`);
        if (isolationInput) isoPoint = getFileName(isolationInput);

        // isolation method
        let isoMethodVal = "";
        const isoMethodEl = div.querySelector(".isolation_method");
        if (isoMethodEl && isoMethodEl.value) {
            if (isoMethodEl.value === "__custom__") {
                const isoCustom = div.querySelector(".isolation_method_custom");
                isoMethodVal = isoCustom ? isoCustom.value.trim() : "";
            } else {
                isoMethodVal = isoMethodEl.value;
            }
        }

        // verification method
        let verMethodVal = "";
        const verMethodEl = div.querySelector(".verification_method");
        if (verMethodEl && verMethodEl.value) {
            if (verMethodEl.value === "__custom__") {
                const verCustom = div.querySelector(".verification_method_custom");
                verMethodVal = verCustom ? verCustom.value.trim() : "";
            } else {
                verMethodVal = verMethodEl.value;
            }
        }

        // verification device
        let verDevice = "";
        const verInput = div.querySelector(`#${CSS.escape(`verification_device_${idx}`)}`);
        if (verInput) verDevice = getFileName(verInput);

        // Build the object in the exact order you want
        const finalSource = {
            device: deviceVal,
            ...(energyVal === "Chemical" && chemicalName ? { chemical_name: chemicalName } : {}),
            ...unitValues, // e.g., psi, volts
            tag: tagVal,
            source_description: descVal,
            isolation_point: isoPoint,
            isolation_method: isoMethodVal,
            verification_method: verMethodVal,
            verification_device: verDevice
        };

        // Only push if at least one key beyond energy_source exists
        const keys = Object.keys(finalSource).filter(k => finalSource[k] !== "" && finalSource[k] != null);
        if (keys.length > 0) {
            sources.push({ energy_source: energyVal, ...finalSource });
        }
    });


    if (sources.length > 0) jsonData["sources"] = sources;

    // write to output textarea if present
    const outputEl = document.getElementById("output");
    if (outputEl) outputEl.value = JSON.stringify(jsonData, null, 2);

    return jsonData;
}



// -----------------------------
// Generate JSON
// -----------------------------
generateButton.addEventListener("click", function() {
    
    const json = generateJSON();
    // console.log(JSON.stringify(json, null, 4));
    outputJSON.value = JSON.stringify(json, null, 4);

});


// -----------------------------
// Download JSON
// -----------------------------
downloadButton.addEventListener("click", () => {
    const json = generateJSON();
    const blob = new Blob([JSON.stringify(json, null, 4)], { type: "application/json" });

    // Determine filename
    const nameInput = document.getElementById("name");
    let filename = nameInput && nameInput.value.trim();
    if (!filename) {
        const today = new Date();
        const y = today.getFullYear();
        const m = String(today.getMonth() + 1).padStart(2, "0");
        const d = String(today.getDate()).padStart(2, "0");
        filename = `${y}${m}${d}_untitledReport`;
    }
    filename += ".json";

    // Trigger download
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    downloadAssets();
});


function downloadAssets() {
  const inputs = document.querySelectorAll('input.image-picker[type="file"]');

  if (![...inputs].some(input => input.files.length > 0)) {
    alert('No files selected in any picker!');
    return;
  }

  inputs.forEach(input => {
    for (const file of input.files) {
      const url = URL.createObjectURL(file);
      const a = document.createElement('a');
      a.href = url;
      a.download = file.name;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  });
}


// -----------------------------
// Auto JSON Generator
// -----------------------------
function setupAutoJSON(inputId) {
    const inputEl = document.getElementById(inputId);
    const outputEl = document.getElementById("output");
    if (!inputEl || !outputEl) return;

    function updateJSON() {
        const json = generateJSON();
        outputEl.value = JSON.stringify(json, null, 4);
    }

    // Trigger JSON update on user input or change
    inputEl.addEventListener("input", updateJSON);
    inputEl.addEventListener("change", updateJSON);

    // If you have a "Today" button for this input, trigger updateJSON when button sets value
    const buttonEl = document.getElementById(inputId + "_button");
    if (buttonEl) {
        buttonEl.addEventListener("click", () => {
            const today = new Date();
            const yyyy = today.getFullYear();
            const mm = String(today.getMonth() + 1).padStart(2, "0");
            const dd = String(today.getDate()).padStart(2, "0");
            inputEl.value = `${yyyy}-${mm}-${dd}`;

            // manually trigger update
            inputEl.dispatchEvent(new Event("input"));
        });
    }
}

// -----------------------------
// Usage Examples
// -----------------------------
setupAutoJSON("completed_date");
setupAutoJSON("approved_by_company");
setupAutoJSON("approved_by"); // or any other input
