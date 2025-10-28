// src/web/scripts/input_form.ts
var sourceCount = 0;
var MAX_SOURCES = 8;
function addSource() {
    if (sourceCount >= MAX_SOURCES) {
        alert("Max ".concat(MAX_SOURCES, " sources allowed"));
        return;
    }
    var container = document.getElementById("sources");
    var div = document.createElement("div");
    div.className = "source";
    div.innerHTML = "\n        <div class=\"source-header\">Source ".concat(sourceCount + 1, "</div>\n        <label>Energy Source: <input type=\"text\" class=\"EnergySource\" /></label>\n        <label>Chemical Name: <input type=\"text\" class=\"ChemicalName\" /></label>\n        <label>Volt: <input type=\"text\" class=\"Volt\" /></label>\n        <label>PSI: <input type=\"text\" class=\"PSI\" /></label>\n        <label>LBS: <input type=\"text\" class=\"LBS\" /></label>\n        <label>Temp: <input type=\"text\" class=\"Temp\" /></label>\n        <label>Device: <input type=\"text\" class=\"Device\" /></label>\n        <label>Tag: <input type=\"text\" class=\"Tag\" /></label>\n        <label>Description: <input type=\"text\" class=\"SourceDescription\" /></label>\n        <label>Isolation Point: <input type=\"text\" class=\"IsolationPoint\" /></label>\n        <label>Isolation Method: <input type=\"text\" class=\"IsolationMethod\" /></label>\n        <label>Verification Method: <input type=\"text\" class=\"VerificationMethod\" /></label>\n        <label>Verification Device: <input type=\"text\" class=\"VerificationDevice\" /></label>\n    ");
    container.appendChild(div);
    sourceCount++;
}
function removeLastSource() {
    if (sourceCount === 0)
        return;
    var container = document.getElementById("sources");
    var lastSource = container.lastElementChild;
    var inputs = lastSource.querySelectorAll("input");
    var hasText = Array.prototype.slice.call(inputs).some(function (i) { return i.value.trim() !== ""; });
    if (hasText && !confirm("The last source contains data. Are you sure you want to remove it?")) {
        return;
    }
    lastSource.remove();
    sourceCount--;
}
function gatherData() {
    var fieldMap = {
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
    var obj = {};
    // Add only non-empty main form fields
    for (var _i = 0, _a = Object.entries(fieldMap); _i < _a.length; _i++) {
        var _b = _a[_i], id = _b[0], key = _b[1];
        var value = getVal(id);
        if (value.trim() !== "") {
            obj[key] = value;
        }
    }
    // Handle sources
    obj.sources = [];
    var sourceDivs = document.querySelectorAll(".source");
    var inputMap = {
        EnergySource: "energy_source",
        ChemicalName: "chemical_name",
        Volt: "volt",
        PSI: "psi",
        LBS: "lbs",
        Temp: "temp",
        Device: "device",
        Tag: "tag",
        SourceDescription: "source_description",
        IsolationPoint: "isolation_point",
        IsolationMethod: "isolation_method",
        VerificationMethod: "verification_method",
        VerificationDevice: "verification_device"
    };
    sourceDivs.forEach(function (div) {
        var s = {};
        div.querySelectorAll("input").forEach(function (input) {
            var key = inputMap[input.className];
            if (key && input.value.trim() !== "") {
                s[key] = input.value;
            }
        });
        // Only push if there is at least one value
        if (Object.keys(s).length > 0) {
            obj.sources.push(s);
        }
    });
    return obj;
}
function generateJSON() {
    var obj = gatherData();
    var output = document.getElementById("output");
    output.value = JSON.stringify(obj, null, 2);
}
function downloadOutput() {
    var output = document.getElementById("output");
    var content = output.value;
    if (!content) {
        alert("Generate the JSON first!");
        return;
    }
    var filename = document.getElementById("name").value.trim() || "data";
    var blob = new Blob([content], { type: "application/json" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = "".concat(filename, ".json");
    a.click();
    URL.revokeObjectURL(url);
}
function getVal(id) {
    var el = document.getElementById(id);
    return (el === null || el === void 0 ? void 0 : el.value) || "";
}
// Attach event listeners after DOM loaded
document.addEventListener("DOMContentLoaded", function () {
    var _a, _b, _c, _d;
    (_a = document.getElementById("addSourceBtn")) === null || _a === void 0 ? void 0 : _a.addEventListener("click", addSource);
    (_b = document.getElementById("removeSourceBtn")) === null || _b === void 0 ? void 0 : _b.addEventListener("click", removeLastSource);
    (_c = document.getElementById("generateBtn")) === null || _c === void 0 ? void 0 : _c.addEventListener("click", generateJSON);
    (_d = document.getElementById("downloadBtn")) === null || _d === void 0 ? void 0 : _d.addEventListener("click", downloadOutput);
});
