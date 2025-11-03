let jsonData = null; // originally loaded JSON data
const updatedFields = {}; // to store changed fields

window.addEventListener("DOMContentLoaded", async () => {
    // Load report JSON first
    jsonData = await loadReportData();

    // Specify fields to track
    const fieldsToTrack = Object.keys(jsonData);
    fieldsToTrack.forEach(field => checkDifference(field));
});

async function loadReportData() {
    try {
        const res = await fetch(`/get_report_json/${window.reportName}`);
        if (!res.ok) throw new Error(`Failed to fetch report JSON: ${res.statusText}`);
        return await res.json();
    } catch (err) {
        console.error(err);
    }
}

function checkDifference(inputID) {
    const element = document.getElementById(inputID);
    if (!element || !jsonData) return;

    // Store the original value for comparison
    const originalValue = jsonData[inputID];

    // Add an event listener for real-time detection of changes
    element.addEventListener("change", () => {
        if (inputID.toLowerCase().includes("date")) {
            const [year, month, day] = element.value.split("-");
            const new_date = month + "/" + day + "/" + year;
            if (new_date !== originalValue) {
                // Store the change
                updatedFields[inputID] = new_date;
                element.classList.add("updated");
            } else {
                // Remove the field if reverted to original
                if (updatedFields.hasOwnProperty(inputID)) {
                    delete updatedFields[inputID];
                    element.classList.remove("updated");
                }
            }
        } else {
            if (element.value !== originalValue) {
                // Store the change
                updatedFields[inputID] = element.value;
                element.classList.add("updated");
            } else {
                // Remove the field if reverted to original
                if (updatedFields.hasOwnProperty(inputID)) {
                    delete updatedFields[inputID];
                    element.classList.remove("updated");
                }
            }
        }
        console.log("Tracked changes:", updatedFields);
    });
}


const updateButton = document.getElementById("updateBtn");

updateButton.addEventListener("click", async () => {
    if (!window.reportName || !updatedFields || Object.keys(updatedFields).length === 0) {
        console.log("No changes to update.");
        return;
    }

    // Convert updatedFields object to an array of {field, value} objects
    const updatesArray = Object.entries(updatedFields).map(([field, value]) => ({
        field,
        value
    }));

    try {
        const res = await fetch("/update_report_json", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                report_name: window.reportName,
                updates: updatesArray
            })
        });

        const data = await res.json();
        console.log("Update response:", data);

        if (res.ok) {
            // Optionally clear tracked changes after successful update
            Object.keys(updatedFields).forEach(k => delete updatedFields[k]);
        }

    } catch (err) {
        console.error("Failed to update report:", err);
    }

    window.location.href = "/update/" + window.reportName;
});


// ===============
// TODAY BUTTON
// ===============

// === Tool: set input to today ===
function todayButton(inputId) {
    const inputElement = document.getElementById(inputId);
    const buttonElement = document.getElementById(inputId + "_button");
    if (!inputElement || !buttonElement) return;

    buttonElement.addEventListener("click", () => {
        const today = new Date();
        const yyyy = today.getFullYear();
        const mm = String(today.getMonth() + 1).padStart(2, "0");
        const dd = String(today.getDate()).padStart(2, "0");
        inputElement.value = `${yyyy}-${mm}-${dd}`;
        inputElement.dispatchEvent(new Event('change'));
    });
}

todayButton("date");
todayButton("completed_date");