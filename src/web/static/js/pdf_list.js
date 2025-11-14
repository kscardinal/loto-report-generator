// pdf_list.js (ES module)
let pendingAction = null; // stored callback for modal confirm

// read initial page/per_page from URL (fallbacks)
let totalPages = 1;  // global total pages
const urlParams = new URLSearchParams(window.location.search);
let currentPage = Math.max(1, parseInt(urlParams.get("page")) || 1);
let perPage = Math.max(1, parseInt(urlParams.get("per_page")) || 25);
let reports = []; // array of all reports

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

// sync select with initial
perPageSelect.value = String(perPage);

// util: update URL without reload
function updateURL() {
    const newUrl = `${window.location.pathname}?page=${currentPage}&per_page=${perPage}`;
    window.history.replaceState(null, "", newUrl);
}

// fetch a page from server
async function fetchPage(page = 1, per_page = perPage) {
    const resp = await fetch(`/pdf_list_json?page=${page}&per_page=${per_page}`, { credentials: "include" });
    if (!resp.ok) {
        console.error("Failed to load reports JSON", resp.status);
        reportListEl.innerHTML = `<p class="no-reports">Failed to load reports (status ${resp.status}).</p>`;
        return null;
    }
    return await resp.json();
}

// render a page response
function renderReportsPage(json) {
    if (!json || !Array.isArray(json.reports)) {
        reportListEl.innerHTML = `<p class="no-reports">No reports found.</p>`;
        pageInfo.textContent = `Page ${currentPage} of 1`;
        paginationInfo.textContent = "";
        prevBtn.disabled = true;
        nextBtn.disabled = true;
        jumpBtn.disabled = true;
        jumpInput.disabled = true;
        return;
    }

    const reports = json.reports;
    const total = json.total || 0;
    const totalPages = json.total_pages || 1;
    const start = (json.page - 1) * json.per_page + 1;
    const end = Math.min(start + reports.length - 1, total);

    // clear
    reportListEl.innerHTML = "";

    // create cards
    reports.forEach((r) => {
        const card = document.createElement("div");
        card.className = "report-card";
        // metadata
        const uploadedBy = r.uploaded_by || "Unknown";
        const tags = Array.isArray(r.tags) ? r.tags.join(", ") : (r.tags || "None");
        const dateUploaded = r.date_added ? new Date(r.date_added).toLocaleString() : "N/A";

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

        // card click -> open report (except when clicking buttons)
        card.addEventListener("click", (ev) => {
            if (ev.target.closest(".download-btn") || ev.target.closest(".delete-btn")) return;
            window.location.href = `/view_report/${encodeURIComponent(r.report_name)}`;
        });

        // keyboard accessibility: Enter opens
        card.addEventListener("keydown", (ev) => {
            if (ev.key === "Enter" && !ev.target.closest(".download-btn") && !ev.target.closest(".delete-btn")) {
                window.location.href = `/view_report/${encodeURIComponent(r.report_name)}`;
            }
        });

        reportListEl.appendChild(card);
    });

    // attach delete handlers (event delegation is OK too)
    document.querySelectorAll(".delete-btn").forEach(btn => {
        btn.addEventListener("click", (ev) => {
            ev.stopPropagation();
            const encodedName = btn.dataset.report;
            const decodedName = decodeURIComponent(encodedName);
            confirmAction(`Delete`, decodedName, () => deleteReport(decodedName));
        });
    });

    // update pagination UI
    pageInfo.textContent = `Page ${json.page} of ${totalPages}`;
    paginationInfo.textContent = `${start}-${end} / ${total}`;
    prevBtn.disabled = json.page <= 1;
    nextBtn.disabled = json.page >= totalPages;
    jumpBtn.disabled = totalPages <= 1;
    jumpInput.disabled = totalPages <= 1;

    // update global trackers
    currentPage = json.page;
    perPage = json.per_page;
    jumpInput.value = currentPage;
    updateURL();

    // After rendering, remove focus from any input/select/button
    if (document.activeElement) {
        document.activeElement.blur();
    }
}

// confirm modal
function confirmAction(actionText, targetName, callbackFn) {
    confirmText.textContent = `Are you sure you want to ${actionText} "${targetName}"?`;
    pendingAction = callbackFn;
    confirmModal.style.display = "flex";
}

// modal button handlers
confirmNo.addEventListener("click", () => {
    pendingAction = null;
    confirmModal.style.display = "none";
});
confirmYes.addEventListener("click", async () => {
    if (pendingAction) {
        await pendingAction();
        pendingAction = null;
    }
    confirmModal.style.display = "none";
    // reload current page
    await loadAndRender(currentPage, perPage);
});

// backend delete
async function deleteReport(reportName) {
    try {
        const resp = await fetch(`/remove_report/${encodeURIComponent(reportName)}`, {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" }
        });
        if (!resp.ok) {
            const data = await resp.json().catch(()=>({}));
            alert(`Failed to delete report: ${data.detail || data.error || resp.status}`);
        } else {
            // Success - refresh
            // If deletion makes current page empty, move back one page if possible
            await loadAndRender(currentPage, perPage);
        }
    } catch (err) {
        console.error("Delete failed", err);
        alert("Delete failed - see console.");
    }
}

async function loadAndRender(page = 1, pp = perPage) {
    perPage = pp;
    const response = await fetch(`/pdf_list_json?per_page=${perPage}`, { credentials: "include" });
    const data = await response.json();
    reports = data.reports;

    totalPages = data.total_pages;
    currentPage = Math.min(Math.max(page, 1), totalPages); // clamp page

    const json = await fetchPage(page, pp);
    renderReportsPage(json);
}

// pagination controls wired
prevBtn.addEventListener("click", async () => {
    if (currentPage > 1) await loadAndRender(currentPage - 1, perPage);
});
nextBtn.addEventListener("click", async () => {
    await loadAndRender(currentPage + 1, perPage);
});
perPageSelect.addEventListener("change", async (e) => {
    perPage = parseInt(e.target.value, 10) || 25;
    currentPage = 1;
    await loadAndRender(currentPage, perPage);
});
jumpBtn.addEventListener("click", async () => {
    let n = parseInt(jumpInput.value, 10);
    if (!isNaN(n)) {
        const maxPage = totalPages; // compute total pages dynamically
        if (n < 1) n = 1;
        else if (n > maxPage) n = maxPage;

        await loadAndRender(n, perPage);
    }
});
jumpInput.addEventListener("keydown", async (e) => {
    if (e.key === "Enter") {
        let n = parseInt(jumpInput.value, 10);
        if (!isNaN(n)) {
            const maxPage = totalPages;
            if (n < 1) n = 1;
            else if (n > maxPage) n = maxPage;

            await loadAndRender(n, perPage);
        }
    }
});

// logout button (call /logout to clear HttpOnly cookie)
const logoutBtn = document.getElementById("logout-btn");
if (logoutBtn) {
    logoutBtn.addEventListener("click", async (ev) => {
        ev.preventDefault();
        try {
            await fetch("/logout", { method: "POST", credentials: "include" });
            window.location.href = "/login";
        } catch (err) {
            console.error("Logout failed", err);
            window.location.href = "/login";
        }
    });
}

// small helper: escape any text for insertion
function escapeHtml(s){
    if (s === null || s === undefined) return "";
    return String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// initial load
loadAndRender(currentPage, perPage);
