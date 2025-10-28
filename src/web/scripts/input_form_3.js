// Action Buttons
var downloadButton = document.getElementById("downloadBtn");
var generateButton = document.getElementById("generateBtn");
// Track the validity of each monitored input field by input ID
var fieldValidity = {
    procedure_number: true,
    revision: true,
    origin: true,
    isolation_points: true
};
var downloadable = false; // overall downloadable flag
// Enables/Disables a single button based on downloadable state
function updateButton(buttonElement) {
    if (!buttonElement)
        return;
    if (downloadable) {
        buttonElement.disabled = false;
        buttonElement.style.cursor = "pointer";
        buttonElement.classList.remove("button-disabled");
    }
    else {
        buttonElement.disabled = true;
        buttonElement.style.cursor = "not-allowed";
        buttonElement.classList.add("button-disabled");
    }
}
// Enables/Disables the download and generate buttons
function updateButtons() {
    updateButton(downloadButton);
    updateButton(generateButton);
}
// Adds input listener for number-only validation, updates validity state and buttons
function checkOnlyNumber(inputId, validityObj) {
    var inputElement = document.getElementById(inputId);
    var labelElement = document.getElementById(inputId + "_label");
    if (!inputElement || !labelElement)
        return;
    inputElement.addEventListener("input", function () {
        var val = inputElement.value;
        var numberOnlyRegex = /^\d+$/;
        if (val.length > 0) {
            var passed = numberOnlyRegex.test(val);
            if (!passed) {
                labelElement.style.display = "block";
                labelElement.textContent = " ❌ Must only be a number";
                inputElement.classList.add("error");
                validityObj[inputId] = false;
            }
            else {
                labelElement.style.display = "none";
                inputElement.classList.remove("error");
                validityObj[inputId] = true;
            }
        }
        else {
            labelElement.style.display = "none";
            inputElement.classList.remove("error");
            // Adjust validity on empty input as per your requirements
            validityObj[inputId] = true;
        }
        // Update overall downloadable state: all fields must be valid
        downloadable = Object.keys(validityObj).every(function (key) { return validityObj[key]; });
        updateButtons();
    });
}
// Initialize validation listeners on all desired fields
checkOnlyNumber("procedure_number", fieldValidity);
checkOnlyNumber("revision", fieldValidity);
checkOnlyNumber("origin", fieldValidity);
checkOnlyNumber("isolation_points", fieldValidity);
// Initially update buttons disabled state according to initial validity
downloadable = Object.keys(fieldValidity).every(function (key) { return fieldValidity[key]; });
updateButtons();
// Optional: add click listeners on buttons with proper type checks
downloadButton === null || downloadButton === void 0 ? void 0 : downloadButton.addEventListener("click", function () {
    console.log("Download Button Pressed!");
});
generateButton === null || generateButton === void 0 ? void 0 : generateButton.addEventListener("click", function () {
    console.log("Generate Button Pressed!");
});
