// -----------------------------
// JSON Energy Data
// -----------------------------
const energyData = {
    "Electric": {
        "inputs": [{filed_name: "volt", unit_name: "volts", title_name: "Volts"}], 
        "device": ["Main Disconnect", "Circuit Breaker Panel"],
        "isolation_method": ["Turn off disconnect and apply personal lock and tag."],
        "verification_method": ["Verify the power has been isolated by pressing the start button on control panel.", "Verify no voltage."]
    },
    "Natural Gas": {
        "inputs": [{filed_name: "psi", unit_name: "psi", title_name: "Pressure"}],
        "device": ["Ball Valve"],
        "isolation_method": ["Close valves, apply cover and personal lock and tag."],
        "verification_method": ["Verify pressure on gauge is zero."]
    },
    "Steam": {
        "inputs": [{filed_name: "psi", unit_name: "psi", title_name: "Pressure"}],
        "device": ["Ball Valve"],
        "isolation_method": ["Close valves, apply cover and personal lock and tag."],
        "verification_method": ["Open drain or bleed of valve.", "Verify pressure on gauge is zero."]
    },
    "Chemical": {
        "inputs": [{filed_name: "psi", unit_name: "psi", title_name: "Pressure"}, {filed_name: "chemical_name", unit_name: "Oxygen", title_name: "Chemical Name"}],
        "device": ["Isolation Valve"],
        "isolation_method": ["Close valves, open bleed valve, apply cover and personal lock and tag."],
        "verification_method": ["Verify zero pressure by checking the pressure gauge.", "Verify no flow."]
    },
    "Hydraulic": {
        "inputs": [{filed_name: "psi", unit_name: "psi", title_name: "Pressure"}],
        "device": ["Isolation Valve", "Isolation and Bleed Valve"],
        "isolation_method": ["Component in down position.", "Cribbing is in place.", "Close valves, open bleed valve, apply cover and personal lock and tag."],
        "verification_method": ["Verify zero pressure by checking the pressure gauge."]
    },
    "Gravity": {
        "inputs": [{filed_name: "lbs", unit_name: "lbs", title_name: "Weight"}],
        "device": ["Lower component to full down position.", "Use cribbing to support component."],
        "isolation_method": ["Component in down position.", "Cribbing is in place."],
        "verification_method": ["Verify equipment is in the down position,", "Verify integrity of cribbing supports."]
    },
    "Thermal": {
        "inputs": [{filed_name: "temp", unit_name: "temperature (°F)", title_name: "Temperature"}],
        "device": ["Steam Coils", "Hot Water", "Residual Burner Heat", "Electric Element", "Cryogenics"],
        "isolation_method": ["Source Dependent, allow time to cool if direct contact is expected.", "Source Dependent, allow time to heat if direct contact is expected."],
        "verification_method": ["Allow sufficient time to cool.", "Verify temp is < 120 °F.", "Verify temp > 35 °F."]
    },
    "Refrigerant": {
        "inputs": [{filed_name: "psi", unit_name: "psi", title_name: "Pressure"}],
        "device": ["Ball Valve"],
        "isolation_method": ["Close valves, apply cover and personal lock and tag."],
        "verification_method": ["Verify zero pressure by checking the pressure gauge."]
    },
    "Water": {
        "inputs": [{filed_name: "psi", unit_name: "psi", title_name: "Pressure"}],
        "device": ["Isolation Valve", "Isolation and Bleed Valve"],
        "isolation_method": ["Component in down position.", "Cribbing is in place.", "Close valves, open bleed valve, apply cover and personal lock and tag."],
        "verification_method": ["Verify zero pressure by checking the pressure gauge."]
    },
    "Pneumatic": {
        "inputs": [{filed_name: "psi", unit_name: "psi", title_name: "Pressure"}],
        "device": ["Ball Valve"],
        "isolation_method": ["Close valves, apply cover and personal lock and tag."],
        "verification_method": ["Verify pressure on gauge is zero."]
    }
};

// helpers ---------------------------------------------------------

// format yyyy-mm-dd or Date -> "MM/DD/YYYY"
function formatDate(value) {
    if (!value) return "";
    // value may already be a Date object or an ISO string yyyy-mm-dd
    let d;
    if (value instanceof Date) d = value;
    else d = new Date(value);
    if (isNaN(d)) return ""; // invalid
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    const yyyy = d.getFullYear();
    return `${mm}/${dd}/${yyyy}`;
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

function generateJSON() {
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
            const field = inpObj.filed_name;
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
            chemical_name: chemicalName,
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
const generateButton = document.getElementById("generateBtn");
const outputJSON = document.getElementById("output");

generateButton.addEventListener("click", function() {
    
    const json = generateJSON();
    // console.log(JSON.stringify(json, null, 4));
    outputJSON.value = JSON.stringify(json, null, 4);

});


// -----------------------------
// Download JSON
// -----------------------------
const downloadButton = document.getElementById("downloadBtn");

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
