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
            } else {
                // Remove the field if reverted to original
                if (updatedFields.hasOwnProperty(inputID)) {
                    delete updatedFields[inputID];
                }
            }
        } else {
            if (element.value !== originalValue) {
            // Store the change
            updatedFields[inputID] = element.value;
            } else {
                // Remove the field if reverted to original
                if (updatedFields.hasOwnProperty(inputID)) {
                    delete updatedFields[inputID];
                }
            }
        }
        console.log("Tracked changes:", updatedFields);
    });
}
