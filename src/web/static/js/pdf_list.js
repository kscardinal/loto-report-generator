let pendingAction = null;

// ------------------------------
// Global variables
// ------------------------------
let totalPages = 1;
let currentPage = 1;
let perPage = 25;
let reports = []; // all reports
let filteredReports = [];

// DOM elements
const searchInput = document.getElementById("searchInput");
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
// Load settings
// ------------------------------
function loadSettings() {
    const savedPage = parseInt(localStorage.getItem("reports_currentPage"), 10);
    const savedPerPage = parseInt(localStorage.getItem("reports_perPage"), 10);
    if (!isNaN(savedPage) && savedPage >= 1) currentPage = savedPage;
    if (!isNaN(savedPerPage) && savedPerPage > 0) perPage = savedPerPage;
    perPageSelect.value = perPage;
}
loadSettings();

function saveSettings() {
    localStorage.setItem("reports_currentPage", currentPage);
    localStorage.setItem("reports_perPage", perPage);
}

// ------------------------------
// Render reports (with search)
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

    // ------------------------------
    // Filter by search
    // ------------------------------
    const query = searchInput.value.trim().toLowerCase();
    filteredReports = query
        ? reports.filter(r =>
            (r.report_name || "").toLowerCase().includes(query) ||
            (r.tags || "").toString().toLowerCase().includes(query) ||
            (r.uploaded_by || "").toLowerCase().includes(query)
        )
        : reports;

    totalPages = json.total_pages || 1;
    currentPage = Math.min(Math.max(json.page || 1, 1), totalPages);
    perPage = json.per_page || perPage;

    const total = filteredReports.length;
    const start = (currentPage - 1) * perPage;
    const end = Math.min(start + perPage, total);

    reportListEl.innerHTML = "";

    filteredReports.slice(start, end).forEach(r => {
        const card = document.createElement("div");
        card.className = "report-card";

        const uploadedBy = r.uploaded_by || "Unknown";
        const tags = Array.isArray(r.tags) ? r.tags.join(", ") : (r.tags || "None");
        const dateUploaded = r.last_modified ? new Date(r.last_modified).toLocaleString("en-US") : "N/A";

        card.innerHTML = `
            <div class="report-info" role="button" tabindex="0" aria-label="Open ${r.report_name}">
                <div class="report-name">${r.report_name}</div>
                <div class="report-meta">${dateUploaded} | Uploaded by: ${uploadedBy}</div>
                <div class="report-meta-line">Tags: ${tags}</div>
            </div>
            <div class="report-buttons">
                <a class="download-btn" href="/download_pdf/${encodeURIComponent(r.report_name)}" title="Download PDF">
                    <img src="/static/includes/download.svg" class="download-btn-symbol" alt="Download">
                </a>
                <button class="delete-btn" data-report="${encodeURIComponent(r.report_name)}" title="Delete report">
                    <img src="/static/includes/trash.svg" class="delete-btn-symbol" alt="Delete">
                </button>
            </div>
        `;

        // click handlers
        card.addEventListener("click", ev => {
            if (ev.target.closest(".download-btn") || ev.target.closest(".delete-btn")) return;
            window.location.href = `/view_report/${encodeURIComponent(r.report_name)}`;
        });

        reportListEl.appendChild(card);
    });

    // attach delete
    document.querySelectorAll(".delete-btn").forEach(btn => {
        btn.onclick = ev => {
            ev.stopPropagation();
            const decodedName = decodeURIComponent(btn.dataset.report);
            confirmAction("Delete", decodedName, () => deleteReport(decodedName));
        };
    });

    // update pagination UI
    pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    paginationInfo.textContent = `${start + 1}-${end} / ${total}`;
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;
    jumpBtn.disabled = totalPages <= 1;
    jumpInput.disabled = totalPages <= 1;
    jumpInput.value = currentPage;

    saveSettings();
}

// ------------------------------
// Search input
// ------------------------------
searchInput.addEventListener("input", debounce(() => {
    currentPage = 1; // optional: reset to first page on search
    renderReportsPage({ 
        reports, 
        total_pages: totalPages, 
        per_page: perPage, 
        page: currentPage 
    });
}, 200));

// ------------------------------
// Load reports from server
// ------------------------------
async function loadAndRender(page = currentPage, pp = perPage) {
    perPage = pp;
    const resp = await fetch(`/pdf_list_json?page=${page}&per_page=${perPage}`, { credentials: "include" });
    const data = await resp.json();
    renderReportsPage(data);
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
    const n = parseInt(jumpInput.value, 10);
    if (!isNaN(n)) await loadAndRender(Math.min(Math.max(n, 1), totalPages), perPage);
});
jumpInput.addEventListener("keydown", async e => {
    if (e.key === "Enter") {
        const n = parseInt(jumpInput.value, 10);
        if (!isNaN(n)) await loadAndRender(Math.min(Math.max(n, 1), totalPages), perPage);
    }
});

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
// Logout
// ------------------------------
if (logoutBtn) {
    logoutBtn.addEventListener("click", async ev => {
        ev.preventDefault();
        try {
            await fetch("/logout", { method: "POST", credentials: "include" });
            window.location.href = "/login";
        } catch {
            window.location.href = "/login";
        }
    });
}

function debounce(fn, delay = 250) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), delay);
    };
}

// ------------------------------
// Initial load
// ------------------------------
loadAndRender();
