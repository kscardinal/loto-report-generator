// pdf_list.js (ES module)
let pendingAction = null; // stored callback for modal confirm

// ------------------------------
// Global variables
// ------------------------------
let totalPages = 1;  
let currentPage = 1;
let perPage = 25;
let reports = []; 

let selectMode = false;
let selectedReports = new Set();

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

const selectModeBtn = document.getElementById("selectModeBtn");
const generateSelectedBtn = document.getElementById("generateSelectedBtn");
const createReportBtn = document.getElementById("createReportBtn");

const selectedCountPopup = document.getElementById("selectedCountPopup");

const renameModal = document.getElementById("renameModal");
const renameInput = document.getElementById("renameInput");
const renameOldName = document.getElementById("renameOldName");
const renameError = document.getElementById("renameError");
const renameYes = document.getElementById("renameYes");
const renameNo = document.getElementById("renameNo");

let pendingRenameAction = null; // stored callback for rename confirmation

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
// Format date helpers
// ------------------------------
function formatETDate(isoStr) {
    if (!isoStr) return "N/A";
    const dt = new Date(isoStr);
    return dt.toLocaleString("en-US", { timeZone: "America/New_York" });
}

function formatFriendlyETDate(isoStr) {
    if (!isoStr) return "N/A";
    const dt = new Date(isoStr);
    const now = new Date();
    const options = { timeZone: "America/New_York" };
    const etDate = new Date(dt.toLocaleString("en-US", options));
    const etNow = new Date(now.toLocaleString("en-US", options));
    const dtDayStart = new Date(etDate.getFullYear(), etDate.getMonth(), etDate.getDate());
    const nowDayStart = new Date(etNow.getFullYear(), etNow.getMonth(), etNow.getDate());
    const diffDays = Math.floor((nowDayStart - dtDayStart) / (1000*60*60*24));
    const timeStr = etDate.toLocaleTimeString("en-US", { hour12: true, hour: "numeric", minute: "2-digit", second: "2-digit" });

    if (diffDays === 0) return `Today, ${timeStr}`;
    if (diffDays === 1) return `Yesterday, ${timeStr}`;
    if (diffDays < 7) return `${etDate.toLocaleDateString("en-US", { weekday: "long" })}, ${timeStr}`;
    if (diffDays < 30) return `${etDate.toLocaleDateString("en-US", { month: "short", day: "numeric" })}, ${timeStr}`;
    return `${etDate.getMonth()+1}/${etDate.getDate()}/${etDate.getFullYear().toString().slice(-2)}, ${timeStr}`;
}

function updateSelectedCountPopup() {
    const count = selectedReports.size;
    if (count > 0) {
        selectedCountPopup.textContent = `${count} report${count === 1 ? "" : "s"} selected`;
        selectedCountPopup.classList.add("show-popup");
        selectedCountPopup.classList.remove("hidden-popup");
        paginationInfo.style.paddingBottom = "50px";
    } else {
        selectedCountPopup.classList.remove("show-popup");
        selectedCountPopup.classList.add("hidden-popup");
        paginationInfo.style.paddingBottom = "0";
    }
}

// ------------------------------
// Render reports page
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
    currentPage = Math.min(Math.max(json.page || 1, 1), totalPages);
    perPage = json.per_page || perPage;

    const total = json.total || reports.length;
    const start = (currentPage - 1) * perPage + 1;
    const end = Math.min(start + reports.length - 1, total);

    reportListEl.innerHTML = "";

    reports.forEach(r => {
        const card = document.createElement("div");
        card.className = "report-card";

        const uploadedBy = r.uploaded_by || "Unknown";
        const tags = Array.isArray(r.tags) ? r.tags.join(", ") : (r.tags || "None");
        const dateUploaded = formatFriendlyETDate(r.last_modified);

        let checkboxHTML = "";
        if (selectMode) {
            checkboxHTML = `
                <input type="checkbox" class="select-checkbox"
                       data-report="${escapeHtml(r.report_name)}"
                       ${selectedReports.has(r.report_name) ? "checked" : ""}>
            `;
        }

        card.innerHTML = `
            ${checkboxHTML}
            <div class="report-info" role="button" tabindex="0" aria-label="Open ${escapeHtml(r.report_name)}">
                <div class="report-name">${escapeHtml(r.report_name)}</div>
                <div class="report-meta">${escapeHtml(dateUploaded)} | Uploaded by: ${escapeHtml(uploadedBy)}</div>
                <div class="report-meta-line">Tags: ${escapeHtml(tags)}</div>
            </div>
            <div class="report-menu-container">
                <button class="menu-btn" data-report="${encodeURIComponent(r.report_name)}" title="More actions">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <circle cx="6" cy="12" r="2.5"/>
                        <circle cx="12" cy="12" r="2.5"/>
                        <circle cx="18" cy="12" r="2.5"/>
                    </svg>
                </button>
                <div class="menu-dropdown" style="display:none;">
                    <a href="#" class="menu-item select-item" title="Enter select mode">
                        Select
                    </a>
                    <a href="/download_pdf/${encodeURIComponent(r.report_name)}" class="menu-item download-item" title="Download PDF" rel="noopener">
                        Download PDF
                    </a>
                    <a href="/download_report_files/${encodeURIComponent(r.report_name)}" class="menu-item download-assets-item" title="Download Assets" rel="noopener">
                        Download Assets
                    </a>
                    <a href="#" class="menu-item rename-item" data-report="${encodeURIComponent(r.report_name)}" title="Rename report">
                        Rename
                    </a>
                    <a href="#" class="menu-item delete-item" data-report="${encodeURIComponent(r.report_name)}" title="Delete report">
                        Delete
                    </a>
                </div>
            </div>
        `;

        if (selectMode) {
            card.classList.add("select-mode");
            const checkbox = card.querySelector(".select-checkbox");
            checkbox.addEventListener("click", ev => {
                ev.stopPropagation();
                const name = ev.target.dataset.report;
                if (ev.target.checked) selectedReports.add(name);
                else selectedReports.delete(name);
                updateSelectedCountPopup();
            });
            card.onclick = ev => { if (!ev.target.classList.contains("select-checkbox")) ev.stopPropagation(); };
        }

        card.addEventListener("click", ev => {
            if (selectMode) return;
            if (ev.target.closest(".report-menu-container")) return;
            window.location.href = `/view_report/${encodeURIComponent(r.report_name)}`;
        });

        card.addEventListener("keydown", ev => {
            if (ev.key === "Enter" && !ev.target.closest(".report-menu-container")) {
                window.location.href = `/view_report/${encodeURIComponent(r.report_name)}`;
            }
        });

        // Menu button handler
        const menuBtn = card.querySelector(".menu-btn");
        const menuDropdown = card.querySelector(".menu-dropdown");
        const menuContainer = card.querySelector(".report-menu-container");
        
        let closeDropdownTimeout;
        
        menuBtn.addEventListener("click", ev => {
            ev.stopPropagation();
            clearTimeout(closeDropdownTimeout);
            // Close all other dropdowns
            document.querySelectorAll(".menu-dropdown").forEach(dropdown => {
                if (dropdown !== menuDropdown) dropdown.style.display = "none";
            });
            // Remove active class from other buttons
            document.querySelectorAll(".menu-btn.active").forEach(btn => {
                if (btn !== menuBtn) btn.classList.remove("active");
            });
            // Toggle this dropdown
            const isOpen = menuDropdown.style.display === "block";
            menuDropdown.style.display = isOpen ? "none" : "block";
            // Toggle active class on button
            if (isOpen) {
                menuBtn.classList.remove("active");
            } else {
                menuBtn.classList.add("active");
            }
        });
        
        // Close dropdown when hovering away from menu container with delay for gap tolerance
        menuContainer.addEventListener("mouseleave", () => {
            closeDropdownTimeout = setTimeout(() => {
                menuDropdown.style.display = "none";
                menuBtn.classList.remove("active");
            }, 100);
        });
        
        // Cancel timeout when re-entering menu container
        menuContainer.addEventListener("mouseenter", () => {
            clearTimeout(closeDropdownTimeout);
        });

        // Select handler
        const selectItem = card.querySelector(".select-item");
        selectItem.addEventListener("click", ev => {
            ev.preventDefault();
            ev.stopPropagation();
            menuDropdown.style.display = "none";
            menuBtn.classList.remove("active");
            selectModeBtn.click();
        });

        // Delete handler
        const deleteBtn = card.querySelector(".delete-item");
        deleteBtn.addEventListener("click", ev => {
            ev.preventDefault();
            ev.stopPropagation();
            const decodedName = decodeURIComponent(deleteBtn.dataset.report);
            menuDropdown.style.display = "none";
            confirmAction("Delete", decodedName, () => deleteReport(decodedName));
        });

        // Rename handler
        const renameBtn = card.querySelector(".rename-item");
        renameBtn.addEventListener("click", ev => {
            ev.preventDefault();
            ev.stopPropagation();
            const decodedName = decodeURIComponent(renameBtn.dataset.report);
            menuDropdown.style.display = "none";
            openRenameModal(decodedName);
        });

        reportListEl.appendChild(card);
    });

    pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    paginationInfo.textContent = `${start}-${end} / ${total}`;
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;
    jumpBtn.disabled = totalPages <= 1;
    jumpInput.disabled = totalPages <= 1;
    jumpInput.value = currentPage;

    updateURL();
    saveSettings();
}

// ------------------------------
// Select mode button
// ------------------------------
selectModeBtn.addEventListener("click", () => {
    selectMode = !selectMode;
    selectedReports.clear();
    selectModeBtn.textContent = selectMode ? "Cancel" : "Select";
    generateSelectedBtn.style.display = selectMode ? "" : "none";
    logoutBtn.style.display = selectMode ? "none" : "";
    createReportBtn.style.display = selectMode ? "none" : "";
    loadAndRender(currentPage, perPage);
    updateSelectedCountPopup();
});

// ------------------------------
// Generate selected button
// ------------------------------
generateSelectedBtn.addEventListener("click", async () => {
    if (selectedReports.size === 0) {
        alert("No reports selected.");
        return;
    }

    const overlay = document.getElementById("pdfGeneratingOverlay");
    overlay.classList.remove("hidden-overlay");

    const list = Array.from(selectedReports);

    try {
        const resp = await fetch("/download_pdf_bulk", {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ reports: list })
        });

        if (!resp.ok) {
            const data = await resp.json().catch(() => ({}));
            alert("Generation failed: " + (data.detail || resp.status));
            return;
        }

        // --------------------------------------------------
        // ✔ Convert the ZIP stream into a blob
        // --------------------------------------------------
        const blob = await resp.blob();

        // --------------------------------------------------
        // ✔ Create a download link for the ZIP
        // --------------------------------------------------
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "bulk_reports.zip";
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);

        // --------------------------------------------------
        // UI cleanup after successful download
        // --------------------------------------------------
        selectMode = false;
        selectedReports.clear();
        updateSelectedCountPopup();
        selectModeBtn.textContent = "Select";
        generateSelectedBtn.style.display = "none";
        await loadAndRender(currentPage, perPage);

    } catch (e) {
        console.error(e);
        alert("Error during generation.");
    }  finally {
        overlay.classList.add("hidden-overlay");
        logoutBtn.style.display = "";
        createReportBtn.style.display = "";
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

// Rename modal handlers
renameNo.addEventListener("click", () => {
    pendingRenameAction = null;
    renameModal.style.display = "none";
    renameInput.value = "";
    renameError.textContent = "";
    renameError.style.display = "none";
});

renameYes.addEventListener("click", async () => {
    const newName = renameInput.value.trim();
    if (!pendingRenameAction) {
        renameError.textContent = "No report selected for renaming.";
        renameError.style.display = "block";
        return;
    }
    const oldName = pendingRenameAction;
    
    // Validation
    if (!newName) {
        renameError.textContent = "Report name cannot be empty.";
        renameError.style.display = "block";
        renameInput.focus();
        return;
    }
    
    if (newName === oldName) {
        renameError.textContent = "New name must be different from the current name.";
        renameError.style.display = "block";
        renameInput.focus();
        return;
    }

    const success = await renameReport(oldName, newName);
    if (success) {
        pendingRenameAction = null; // only clear if rename succeeded
    }
});

renameInput.addEventListener("keydown", async e => {
    if (e.key === "Enter") {
        e.preventDefault();
        const newName = renameInput.value.trim();
        if (!pendingRenameAction) {
            renameError.textContent = "No report selected for renaming.";
            renameError.style.display = "block";
            return;
        }
        const oldName = pendingRenameAction;
        
        // Validation
        if (!newName) {
            renameError.textContent = "Report name cannot be empty.";
            renameError.style.display = "block";
            renameInput.focus();
            return;
        }
        
        if (newName === oldName) {
            renameError.textContent = "New name must be different from the current name.";
            renameError.style.display = "block";
            renameInput.focus();
            return;
        }

        const success = await renameReport(oldName, newName);
        if (success) {
            pendingRenameAction = null; // only clear if rename succeeded
        }
    } else if (e.key === "Escape") {
        e.preventDefault();
        pendingRenameAction = null;
        renameModal.style.display = "none";
        renameInput.value = "";
        renameError.textContent = "";
        renameError.style.display = "none";
    }
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
// Open rename modal
// ------------------------------
function openRenameModal(reportName) {
    renameOldName.textContent = `Current name: "${reportName}"`;
    renameInput.value = reportName;
    renameError.textContent = "";
    renameError.style.display = "none";
    renameModal.style.display = "flex";
    renameInput.focus();
    renameInput.select();
    
    pendingRenameAction = reportName;
}

// ------------------------------
// Rename report
// ------------------------------
async function renameReport(oldName, newName) {
    try {
        const resp = await fetch("/rename_report", {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ old_name: oldName, new_name: newName })
        });
        if (!resp.ok) {
            const data = await resp.json().catch(() => ({}));
            renameError.textContent = data.detail || data.error || "Failed to rename report";
            renameError.style.display = "block";
            return false; // indicate failure
        } else {
            renameModal.style.display = "none";
            await loadAndRender(currentPage, perPage);
            return true; // indicate success
        }
    } catch (err) {
        console.error(err);
        renameError.textContent = "Rename failed - see console";
        renameError.style.display = "block";
        return false; // indicate failure
    }
}

// ------------------------------
// Load and render
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

// ------------------------------
// Close modal with Escape key
// ------------------------------
document.addEventListener("keydown", (e) => {
	// Check if the Escape key was pressed and the modal is currently visible
	if (e.key === "Escape") {
		// Close confirm modal
		if (confirmModal.style.display === "flex") {
			e.preventDefault(); 
			pendingAction = null;
			confirmModal.style.display = "none";
		}
		// Close rename modal
		else if (renameModal.style.display === "flex") {
			e.preventDefault();
			pendingRenameAction = null;
			renameModal.style.display = "none";
			renameInput.value = "";
			renameError.textContent = "";
			renameError.style.display = "none";
		}
		// Exit select mode
		else if (selectMode) {
			e.preventDefault();
			selectModeBtn.click();
		}
		// Close menu dropdowns
		else {
			document.querySelectorAll(".menu-dropdown").forEach(dropdown => {
				if (dropdown.style.display === "block") {
					dropdown.style.display = "none";
				}
			});
		}
	}
});

// ------------------------------
// Close menu dropdowns when clicking outside
// ------------------------------
document.addEventListener("click", () => {
    document.querySelectorAll(".menu-dropdown").forEach(dropdown => {
        dropdown.style.display = "none";
    });
});