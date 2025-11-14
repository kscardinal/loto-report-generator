// pdf_list.js (ES module)
let pendingAction = null; // stored callback for modal confirm

// ------------------------------
// Global variables
// ------------------------------
let totalPages = 1;  // global total pages
let currentPage = 1;
let perPage = 25;
let reports = []; // array of all reports

// DOM elements
const reportListEl = document.getElementById("reportList");
const perPageSelect = document.getElementById("perPageSelect");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
const pageInfo = document.getElementById("pageInfo");
const paginationInfo = document.getElementById("paginationInfo");
const jumpInput = document.getElementById("jumpPageInput");
const jumpBtn = document.getElementById("jumpPageBtn");
const confirmModal = document.getElementById("confirmModal");
const confirmText = document.getElementById("confirmText");
const confirmYes = document.getElementById("confirmYes");
const confirmNo = document.getElementById("confirmNo");
const logoutBtn = document.getElementById("logout-btn");

// ------------------------------
// Load settings from localStorage
// ------------------------------
function loadSettings() {
    const savedPage = parseInt(localStorage.getItem("reports_currentPage"), 10);
    const savedPerPage = parseInt(localStorage.getItem("reports_perPage"), 10);

    if (!isNaN(savedPage) && savedPage >= 1) currentPage = savedPage;
    if (!isNaN(savedPerPage) && savedPerPage > 0) perPage = savedPerPage;

    perPageSelect.value = perPage;
}
loadSettings();

// ------------------------------
// Save settings to localStorage
// ------------------------------
function saveSettings() {
    localStorage.setItem("reports_currentPage", currentPage);
    localStorage.setItem("reports_perPage", perPage);
}

// ------------------------------
// Utility: update URL
// ------------------------------
function updateURL() {
    const newUrl = `${window.location.pathname}?page=${currentPage}&per_page=${perPage}`;
    window.history.replaceState(null, "", newUrl);
}

// ------------------------------
// Format date in ET timezone
// ------------------------------
function formatETDate(isoStr) {
    if (!isoStr) return "N/A";
    const dt = new Date(isoStr);
    return dt.toLocaleString("en-US", { timeZone: "America/New_York" });
}

// ------------------------------
// Format date friendly
// ------------------------------
function formatFriendlyETDate(isoStr) {
    if (!isoStr) return "N/A";

    const dt = new Date(isoStr);
    const now = new Date();

    // Convert to ET offset (New York)
    const options = { timeZone: "America/New_York" };
    const etDate = new Date(dt.toLocaleString("en-US", options));
    const etNow = new Date(now.toLocaleString("en-US", options));

    // Differences
    const dtDayStart = new Date(etDate.getFullYear(), etDate.getMonth(), etDate.getDate());
    const nowDayStart = new Date(etNow.getFullYear(), etNow.getMonth(), etNow.getDate());
    const diffDays = Math.floor((nowDayStart - dtDayStart) / (1000*60*60*24));

    // Time part
    const timeStr = etDate.toLocaleTimeString("en-US", { hour12: true, hour: "numeric", minute: "2-digit", second: "2-digit" });

    if (diffDays === 0) return `Today, ${timeStr}`;
    if (diffDays === 1) return `Yesterday, ${timeStr}`;
    if (diffDays < 7) return `${etDate.toLocaleDateString("en-US", { weekday: "long" })}, ${timeStr}`;
    if (diffDays < 30) return `${etDate.toLocaleDateString("en-US", { month: "short", day: "numeric" })}, ${timeStr}`;
    
    // For 30+ days ago, show full numeric date
    return `${etDate.getMonth()+1}/${etDate.getDate()}/${etDate.getFullYear().toString().slice(-2)}, ${timeStr}`;
}

// ------------------------------
// Render a page of reports
// ------------------------------
function renderReportsPage(json) {
    if (!json || !Array.isArray(json.reports)) {
        reportListEl.innerHTML = `<p class="no-reports">No reports found.</p>`;
        pageInfo.textContent = `Page 1 of 1`;
        paginationInfo.textContent = "";
        prevBtn.disabled = true;
        nextBtn.disabled = true;
        jumpBtn.disabled = true;
        jumpInput.disabled = true;
        return;
    }

    reports = json.reports;
    totalPages = json.total_pages || 1;

    // Clamp currentPage if necessary
    currentPage = Math.min(Math.max(json.page || 1, 1), totalPages);

    const start = (currentPage - 1) * perPage + 1;
    const end = Math.min(start + reports.length - 1, json.total || reports.length);

    reportListEl.innerHTML = "";
    reports.forEach(r => {
        const card = document.createElement("div");
        card.className = "report-card";

        const uploadedBy = r.uploaded_by || "Unknown";
        const tags = Array.isArray(r.tags) ? r.tags.join(", ") : (r.tags || "None");
        const dateUploaded = formatFriendlyETDate(r.last_modified);

        card.innerHTML = `
            <div class="report-info" role="button" tabindex="0" aria-label="Open ${escapeHtml(r.report_name)}">
                <div class="report-name">${escapeHtml(r.report_name)}</div>
                <div class="report-meta">${escapeHtml(dateUploaded)} | Uploaded by: ${escapeHtml(uploadedBy)}</div>
                <div class="report-meta-line">Tags: ${escapeHtml(tags)}</div>
            </div>
            <div class="report-buttons">
                <a class="download-btn" href="/download_pdf/${encodeURIComponent(r.report_name)}" title="Download PDF" rel="noopener">
                    <img src="/static/includes/download.svg" class="download-btn-symbol" alt="Download">
                </a>
                <button class="delete-btn" data-report="${encodeURIComponent(r.report_name)}" title="Delete report">
                    <img src="/static/includes/trash.svg" class="delete-btn-symbol" alt="Delete">
                </button>
            </div>
        `;

        card.addEventListener("click", ev => {
            if (ev.target.closest(".download-btn") || ev.target.closest(".delete-btn")) return;
            window.location.href = `/view_report/${encodeURIComponent(r.report_name)}`;
        });

        card.addEventListener("keydown", ev => {
            if (ev.key === "Enter" && !ev.target.closest(".download-btn") && !ev.target.closest(".delete-btn")) {
                window.location.href = `/view_report/${encodeURIComponent(r.report_name)}`;
            }
        });

        reportListEl.appendChild(card);
    });

    // Attach delete handlers
    document.querySelectorAll(".delete-btn").forEach(btn => {
        btn.onclick = ev => {
            ev.stopPropagation();
            const decodedName = decodeURIComponent(btn.dataset.report);
            confirmAction("Delete", decodedName, () => deleteReport(decodedName));
        };
    });

    // Update pagination UI
    pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    paginationInfo.textContent = `${start}-${end} / ${json.total || reports.length}`;
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;
    jumpBtn.disabled = totalPages <= 1;
    jumpInput.disabled = totalPages <= 1;
    jumpInput.value = currentPage;

    updateURL();
    saveSettings();

    // blur focused element to avoid aria-hidden issues
    if (document.activeElement) document.activeElement.blur();
}

// ------------------------------
// Confirm modal
// ------------------------------
function confirmAction(actionText, targetName, callbackFn) {
    confirmText.textContent = `Are you sure you want to ${actionText} "${targetName}"?`;
    pendingAction = callbackFn;
    confirmModal.style.display = "flex";
}

confirmNo.addEventListener("click", () => {
    pendingAction = null;
    confirmModal.style.display = "none";
});

confirmYes.addEventListener("click", async () => {
    if (pendingAction) await pendingAction();
    pendingAction = null;
    confirmModal.style.display = "none";
    await loadAndRender(currentPage, perPage);
});

// ------------------------------
// Delete report
// ------------------------------
async function deleteReport(reportName) {
    try {
        const resp = await fetch(`/remove_report/${encodeURIComponent(reportName)}`, {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" }
        });
        if (!resp.ok) {
            const data = await resp.json().catch(() => ({}));
            alert(`Failed to delete report: ${data.detail || data.error || resp.status}`);
        } else {
            await loadAndRender(currentPage, perPage);
        }
    } catch (err) {
        console.error(err);
        alert("Delete failed - see console.");
    }
}

// ------------------------------
// Load and render
// ------------------------------
async function loadAndRender(page = currentPage, pp = perPage) {
    perPage = pp;

    const resp = await fetch(`/pdf_list_json?per_page=${perPage}`, { credentials: "include" });
    const data = await resp.json();
    reports = data.reports || [];

    totalPages = data.total_pages || Math.ceil((reports.length || 1) / perPage);
    currentPage = Math.min(Math.max(page, 1), totalPages);

    renderReportsPage({
        reports: reports.slice((currentPage - 1) * perPage, currentPage * perPage),
        total: reports.length,
        page: currentPage,
        per_page: perPage,
        total_pages: totalPages
    });
}

// ------------------------------
// Pagination controls
// ------------------------------
prevBtn.addEventListener("click", async () => { if (currentPage > 1) await loadAndRender(currentPage - 1, perPage); });
nextBtn.addEventListener("click", async () => { if (currentPage < totalPages) await loadAndRender(currentPage + 1, perPage); });

perPageSelect.addEventListener("change", async e => {
    perPage = parseInt(e.target.value, 10) || 25;
    currentPage = 1;
    await loadAndRender(currentPage, perPage);
});

jumpBtn.addEventListener("click", async () => {
    let n = parseInt(jumpInput.value, 10);
    if (!isNaN(n)) {
        n = Math.min(Math.max(n, 1), totalPages);
        await loadAndRender(n, perPage);
    }
});

jumpInput.addEventListener("keydown", async e => {
    if (e.key === "Enter") {
        let n = parseInt(jumpInput.value, 10);
        if (!isNaN(n)) {
            n = Math.min(Math.max(n, 1), totalPages);
            await loadAndRender(n, perPage);
        }
    }
});

// ------------------------------
// Logout button
// ------------------------------
if (logoutBtn) {
    logoutBtn.addEventListener("click", async ev => {
        ev.preventDefault();
        try {
            await fetch("/logout", { method: "POST", credentials: "include" });
            window.location.href = "/login";
        } catch (err) {
            console.error(err);
            window.location.href = "/login";
        }
    });
}

// ------------------------------
// Escape HTML helper
// ------------------------------
function escapeHtml(s) {
    if (s === null || s === undefined) return "";
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
                     .replace(/>/g, "&gt;").replace(/"/g, "&quot;")
                     .replace(/'/g, "&#039;");
}

// ------------------------------
// Initial load
// ------------------------------
loadAndRender(currentPage, perPage);
