// -----------------------------
// Helper Functions
// -----------------------------

// Utility: format a date input (YYYY-MM-DD) to MM/DD/YYYY
function formatDate(inputValue) {
    if (!inputValue) return "";
    const [year, month, day] = inputValue.split("-");
    return `${month}/${day}/${year}`;
}

// Utility: get filename from a file input
function getFileName(inputElement) {
    if (!inputElement || !inputElement.files || inputElement.files.length === 0) return "";
    return inputElement.files[0].name;
}

// Main function: collects all input values and returns a JSON object
function generateJSON() {
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

    fields.forEach((id) => {
        const input = document.getElementById(id);
        if (!input) return;

        // Handle special cases
        if (input.type === "date") {
            jsonData[id] = formatDate(input.value);
        } else if (input.type === "file") {
            jsonData[id] = getFileName(input);
        } else {
            jsonData[id] = input.value || "";
        }
    });

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
