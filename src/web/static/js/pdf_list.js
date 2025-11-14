let pendingAction = null;  // For delete confirmations

/** -----------------------------
 *   Fetch and Render Reports
----------------------------- */
async function fetchReports() {
    const response = await fetch("/pdf_list_json", { credentials: "include" });
    const data = await response.json();
    const container = document.getElementById("reportList");
    container.innerHTML = "";

    // Sort reports by date_added descending
    data.reports.sort((a, b) => new Date(b.date_added) - new Date(a.date_added));

    data.reports.forEach((report, index) => {
        const div = document.createElement("div");
        div.classList.add("report-card");

        const uploadedBy = report.uploaded_by || "Unknown";
        const tags = report.tags ? report.tags.join(", ") : "None";
        const dateUploaded = report.date_added ? new Date(report.date_added).toLocaleString() : "N/A";


        div.innerHTML = `
            <div class="report-info">
                <div class="report-name">${report.report_name}</div>
                <div class="report-meta">Date: ${dateUploaded}</div>
                <div class="report-meta">Uploaded by: ${uploadedBy}</div>
                <div class="report-meta">Tags: ${tags}</div>
            </div>
            <div class="report-buttons">
                <a class="download-btn" href="/download_pdf/${report.report_name}" title="Download PDF">
                    <img src="/static/includes/downloadSymbol.svg" class="download-btn-symbol" alt="Download">
                </a>
                <button class="delete-btn" data-report="${report.report_name}">
                    <img src="/static/includes/trashSymbol.svg" class="delete-btn-symbol" alt="Delete">
                </button>
            </div>
        `;

        // Make the whole card clickable except buttons
        div.addEventListener("click", e => {
            if (!e.target.closest(".download-btn") && !e.target.closest(".delete-btn")) {
                window.location.href = `/view_report/${report.report_name}`;
            }
        });

        container.appendChild(div);
    });

    // Attach delete button handlers
    document.querySelectorAll(".delete-btn").forEach(btn => {
        btn.onclick = () => confirmAction("Delete", btn.dataset.report, deleteReport);
    });
}

/** -----------------------------
 *   Confirmation Modal Logic
----------------------------- */
function confirmAction(actionText, reportName, callbackFn) {
    const modal = document.getElementById("confirmModal");
    const text = document.getElementById("confirmText");

    text.textContent = `Are you sure you want to ${actionText} "${reportName}"?`;
    modal.style.display = "flex";

    pendingAction = () => callbackFn(reportName);
}

document.getElementById("confirmNo").onclick = () => {
    pendingAction = null;
    document.getElementById("confirmModal").style.display = "none";
};

document.getElementById("confirmYes").onclick = async () => {
    if (pendingAction) await pendingAction();
    document.getElementById("confirmModal").style.display = "none";
    pendingAction = null;
    fetchReports();
};

/** -----------------------------
 *   Backend Call
----------------------------- */
async function deleteReport(reportName) {
    const response = await fetch(`/remove_report/${reportName}`, { method: "POST", credentials: "include" });
    if (!response.ok) {
        const data = await response.json();
        alert(`Failed to delete report: ${data.error || JSON.stringify(data)}`);
    }
}

// Initial fetch
fetchReports();
