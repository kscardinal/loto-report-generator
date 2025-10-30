console.log("upload_json.js");

import { generateJSON } from './json_handlers.js';

// -----------------------------
// Upload JSON + images
// -----------------------------
const uploadButton = document.getElementById("uploadBtn");

uploadButton.addEventListener("click", async () => {
    // Always regenerate JSON from the current form
    const jsonValue = generateJSON(); // returns a stringified JSON

    console.log("Generated JSON:", jsonValue);

    // Determine report name
    const nameInput = document.getElementById("name");
    let reportName = nameInput && nameInput.value.trim();
    if (!reportName) {
        const today = new Date();
        const y = today.getFullYear();
        const m = String(today.getMonth() + 1).padStart(2, "0");
        const d = String(today.getDate()).padStart(2, "0");
        reportName = `${y}${m}${d}_untitledReport`;
    } else {
        reportName = await getUniqueReportName(nameInput.value.trim());
    }

    console.log(reportName);

    // Create FormData
    const formData = new FormData();

    // Append JSON as a file
    const jsonBlob = new Blob([JSON.stringify(jsonValue)], { type: "application/json" });
    formData.append("files", jsonBlob, `${reportName}.json`);

    // Append all selected images
    const inputs = document.querySelectorAll('input.image-picker[type="file"]');
    inputs.forEach(input => {
        for (const file of input.files) {
            formData.append("files", file, file.name);
        }
    });

    // Add metadata
    formData.append("uploaded_by", "Web App");
    ["web"].forEach(tag => formData.append("tags", tag));
    formData.append("notes", "This was uploaded from the web");

    // Send request
    try {
        const response = await fetch("/upload/", {
            method: "POST",
            body: formData
        });

        const data = await response.json();
        if (response.ok) {
            alert(`Upload successful! Report: ${data.report_name}\nFiles: ${data.photos.join(", ")}`);
            window.location.href = "/pdf_list";  // <-- redirects user
        } else {
            alert(`Upload failed: ${data.error || JSON.stringify(data)}`);
        }
    } catch (err) {
        console.error(err);
        alert("Upload failed: see console for details.");
    }
});


// -----------------------------
// Checks for duplicates and numbers them accordingly
// -----------------------------
async function getUniqueReportName(baseName) {
    let name = baseName;
    let counter = 1;

    const response = await fetch(`/pdf_list_json`);
    const data = await response.json();
    const existingNames = data.reports.map(r => r.report_name);

    while (existingNames.includes(name)) {
        name = `${baseName}_${counter}`;
        counter++;
    }

    return name;
}
