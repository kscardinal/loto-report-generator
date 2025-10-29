console.log("upload_json.js");

// -----------------------------
// Upload JSON + images
// -----------------------------
const uploadButton = document.getElementById("uploadBtn");
const outputJSON = document.getElementById("output");

uploadButton.addEventListener("click", async () => {
    // Optional confirmation (can remove later)
    if (!confirm("Are you sure you want to upload this report?")) return;

    // Check that JSON exists
    const jsonValue = outputJSON.value.trim();
    if (!jsonValue) {
        alert("JSON is empty! Generate the report first.");
        return;
    }

    // Determine report name
    const nameInput = document.getElementById("name");
    let reportName = nameInput && nameInput.value.trim();
    if (!reportName) {
        const today = new Date();
        const y = today.getFullYear();
        const m = String(today.getMonth() + 1).padStart(2, "0");
        const d = String(today.getDate()).padStart(2, "0");
        reportName = `${y}${m}${d}_untitledReport`;
    }

    // Create FormData
    const formData = new FormData();

    // Append JSON as a file with proper name
    const jsonBlob = new Blob([jsonValue], { type: "application/json" });
    formData.append("files", jsonBlob, `${reportName}.json`);

    // Append all selected images (base filename only)
    const inputs = document.querySelectorAll('input.image-picker[type="file"]');
    inputs.forEach(input => {
        for (const file of input.files) {
            formData.append("files", file, file.name); // file.name only
        }
    });

    // Add metadata
    formData.append("uploaded_by", "Web App");
    //formData.append("tags", "web"); // just "web"
    const tags = ["web"];
    tags.forEach(tag => formData.append("tags", tag));
    formData.append("notes", "This was uploaded from the web");

    // Send request
    try {
        const response = await fetch("http://localhost:8000/upload/", {
            method: "POST",
            body: formData
        });

        const data = await response.json();
        if (response.ok) {
            alert(`Upload successful! Report: ${data.report_name}\nFiles: ${data.photos.join(", ")}`);
        } else {
            alert(`Upload failed: ${data.error || JSON.stringify(data)}`);
        }
    } catch (err) {
        console.error(err);
        alert("Upload failed: see console for details.");
    }
});
