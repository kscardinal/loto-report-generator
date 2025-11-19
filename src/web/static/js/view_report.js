// view_report.js - moved from inline template

let pendingAction = null; // Stored callback for modal confirm

// DOM elements for Modal (NEW)
const confirmModal = document.getElementById("confirmModal");
const confirmText = document.getElementById("confirmText");
const confirmYes = document.getElementById("confirmYes");
const confirmNo = document.getElementById("confirmNo");

// ------------------------------
// Confirm modal (NEW)
// ------------------------------
function confirmAction(actionText, targetName, callbackFn) {
    confirmText.textContent = `Are you sure you want to ${actionText} "${targetName}"?`;
    pendingAction = callbackFn;
    confirmModal.style.display = "flex";
}

if (confirmNo) {
    confirmNo.addEventListener("click", () => {
        pendingAction = null;
        confirmModal.style.display = "none";
    });
}

if (confirmYes) {
    confirmYes.addEventListener("click", async () => {
        if (pendingAction) await pendingAction();
        pendingAction = null;
        confirmModal.style.display = "none";
        // After successful deletion, the deleteReport function will handle redirect
    });
}

// ------------------------------
// Delete report (UPDATED)
// ------------------------------
async function deleteReport(reportName, redirectUrl) {
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
            // Success: Redirect to list page
            console.log("Report deleted successfully, redirecting...");
            if (redirectUrl) window.location.href = redirectUrl; else window.location.reload();
        }
    } catch (err) {
        console.error(err);
        alert("Delete failed - see console.");
    }
}


function loadScript(url) {
    return new Promise((resolve, reject) => {
        const s = document.createElement('script');
        s.src = url;
        s.onload = () => resolve();
        s.onerror = (e) => reject(new Error(`Failed to load ${url}`));
        document.head.appendChild(s);
    });
}

// --------------------------------------------------------
// --- DATE UTILITY FUNCTIONS (MOVED TO GLOBAL SCOPE) ---
// --------------------------------------------------------

// --- Helper function to add ordinal suffix (st, nd, rd, th) ---
function getOrdinalDate(date) {
    const day = date.getDate();
    if (day > 3 && day < 21) return day + 'th'; // 11th, 12th, 13th, etc.
    switch (day % 10) {
        case 1: return day + 'st';
        case 2: return day + 'nd';
        case 3: return day + 'rd';
        default: return day + 'th';
    }
}

function formatFriendlyETDate(isoStr) { 
    if (!isoStr) return "N/A";
    
    // 1. CLEAN THE DATE STRING
    const cleanIsoStr = isoStr.replace(/\.\d{3,}(\+00:00)?/, 'Z');

    const dt = new Date(cleanIsoStr);
    
    // Validate the date object
    if (isNaN(dt.getTime())) { 
        console.error("Date constructor failed on string:", cleanIsoStr);
        return "Invalid Date";
    }
    
    const now = new Date();
    const ET_OPTIONS = { timeZone: "America/New_York" };

    // --- Day Difference Calculation (based on ET midnight) ---
    const getDateComponent = (dateObj, part) => {
        return dateObj.toLocaleString('en-US', { [part]: 'numeric', ...ET_OPTIONS });
    };

    const dtYear = getDateComponent(dt, 'year');
    const dtMonth = getDateComponent(dt, 'month');
    const dtDay = getDateComponent(dt, 'day');

    const nowYear = getDateComponent(now, 'year');
    const nowMonth = getDateComponent(now, 'month');
    const nowDay = getDateComponent(now, 'day');

    // Create Date objects representing the start of the day in ET (00:00:00)
    const dtDayStart = new Date(`${dtYear}-${dtMonth}-${dtDay}T00:00:00`); 
    const nowDayStart = new Date(`${nowYear}-${nowMonth}-${nowDay}T00:00:00`); 
    
    // Calculate difference in full days
    const diffTime = nowDayStart.getTime() - dtDayStart.getTime();
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    // --- Formatting ---
    const timeStr = dt.toLocaleTimeString("en-US", { 
        hour12: true, 
        hour: "numeric", 
        minute: "2-digit", 
        second: "2-digit",
        ...ET_OPTIONS
    });

    const numericDateET = dt.toLocaleDateString("en-US", { 
        month: "2-digit", 
        day: "2-digit", 
        year: "2-digit", 
        ...ET_OPTIONS
    });

    if (diffDays === 0) {
        return `Today (${numericDateET}) at ${timeStr.toLowerCase()}`;
    }
    if (diffDays === 1) {
        return `Yesterday (${numericDateET}) at ${timeStr.toLowerCase()}`;
    }
    
    if (diffDays < 7) {
        const weekday = dt.toLocaleDateString("en-US", { weekday: "long", ...ET_OPTIONS });
        return `${weekday} (${numericDateET}) at ${timeStr.toLowerCase()}`;
    }
    
    const monthYearStr = dt.toLocaleDateString("en-US", { 
        month: "long", 
        year: "numeric", 
        ...ET_OPTIONS 
    });

    const ordinalDay = getOrdinalDate(dt);
    const friendlyDate = `${monthYearStr.split(' ')[0]} ${ordinalDay}, ${monthYearStr.split(' ')[1]}`;
    return `${friendlyDate} at ${timeStr.toLowerCase()}`;
}

// --- Dynamic Date Update Helper (MOVED TO GLOBAL SCOPE) ---
function updateDateDisplay(id, newIsoDate) {
    // formatFriendlyETDate is now globally accessible
    const element = document.getElementById(id);
    if (element) {
        // 1. Update the raw data attribute
        element.dataset.rawDate = newIsoDate;
        
        // 2. Re-format and update the displayed text
        const formattedDate = formatFriendlyETDate(newIsoDate);
        // Assuming the label is wrapped in <strong> for extraction
        const labelElement = element.querySelector('strong'); 
        const label = labelElement ? labelElement.textContent : 'Last Generated: ';
        
        element.innerHTML = `<strong>${label}</strong> ${formattedDate}`;
        console.log(`Updated ${id} to: ${formattedDate}`);
    }
}
// --------------------------------------------------------

async function initPdfViewer() {
    console.log("Initializing PDF viewer...");

    // Ensure pdfjsLib is available.
    if (typeof window.pdfjsLib === 'undefined') {
        console.warn('pdfjsLib not found; loading fallback UMD build from cdnjs...');
        await loadScript('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.14.305/pdf.min.js');
        window.pdfjsLib = window.pdfjsLib || window.pdfjsDistPdfjs || window['pdfjs-dist/build/pdf'];
        if (!window.pdfjsLib) {
            console.error('Fallback PDF.js did not expose pdfjsLib');
            return;
        }
        window.pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.14.305/pdf.worker.min.js';
    } else {
        window.pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.14.305/pdf.worker.min.js';
    }

    const pdfViewer = document.getElementById("pdfViewer");
    const pdfLoading = document.getElementById("pdfLoading");
    const reportName = document.body.dataset.reportName;
    const redirectUrl = document.body.dataset.redirectUrl;
    const pdfUrl = `/download_pdf/${reportName}`;
    let pdfDoc = null;
    let currentScale = 1.1;
    let cachedPdfBlob = null; // cached blob for quick downloads

    // Grab the download anchor and keep it disabled until we have the blob
    const downloadAnchor = document.getElementById('downloadPdfAnchor');
    if (downloadAnchor) {
        downloadAnchor.classList.add('disabled');
        downloadAnchor.setAttribute('aria-disabled', 'true');
        // prevent accidental navigation even if href exists
        downloadAnchor.addEventListener('click', (e) => {
            e.preventDefault();
            if (!cachedPdfBlob) {
                // Inform the user politely that generation is in progress
                const prev = downloadAnchor.textContent;
                downloadAnchor.textContent = 'Generating…';
                setTimeout(()=> downloadAnchor.textContent = prev, 1200);
                return;
            }
            // if cached, trigger download
            downloadCachedPdf();
        });
    }

    // Fetch PDF as blob, load into PDF.js from memory (ArrayBuffer)
    async function loadPdf() {
        console.log("Starting PDF load:", pdfUrl);
        
        // Get the <p> element within pdfLoading to update the text *only*, 
        const loadingText = pdfLoading ? pdfLoading.querySelector('p') : null;

        if (loadingText) loadingText.textContent = "Loading PDF ...";
        
        try {
            const resp = await fetch(pdfUrl, { credentials: 'include' });
            if (!resp.ok) {
                const txt = await resp.text().catch(() => null);
                throw new Error(txt || `HTTP ${resp.status}`);
            }

            const blob = await resp.blob();
            cachedPdfBlob = blob;
            const arrayBuffer = await blob.arrayBuffer();

            // 🌟 FETCH UPDATED METADATA 🌟
            try {
                // Call your existing metadata endpoint
                const metadataResp = await fetch(`/metadata/${encodeURIComponent(reportName)}`, { credentials: 'include' });
                if (metadataResp.ok) {
                    const metadata = await metadataResp.json();
                    
                    // Update the Last Generated date field in the DOM
                    if (metadata.last_generated) {
                        updateDateDisplay("lastGenerated", metadata.last_generated);
                    }
                } else {
                    console.warn("Could not fetch updated metadata. Status:", metadataResp.status);
                }
            } catch (metaErr) {
                console.error("Error fetching report metadata:", metaErr);
            }
            // 🌟 END METADATA FETCH 🌟

            // Load PDF from in-memory data to avoid another network request
            const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer });
            pdfDoc = await loadingTask.promise;
            console.log("PDF loaded from blob. Number of pages:", pdfDoc.numPages);

            // Remove loading message (including the spinner) and render
            if (pdfLoading) pdfLoading.remove();
            renderAllPages();

            // Enable the download anchor now that we have the blob
            if (downloadAnchor) {
                downloadAnchor.classList.remove('disabled');
                document.getElementById('downloadBtn').classList.remove('disabled');
                document.getElementById('deleteBtn').classList.remove('disabled');
                downloadAnchor.setAttribute('aria-disabled', 'false');
            }

        } catch (err) {
            console.error("Error loading PDF:", err);
            
            // Handle error
            if (pdfLoading) {
                const spinner = pdfLoading.querySelector('.spinner');
                if (spinner) spinner.remove();

                if (loadingText) {
                    loadingText.textContent = "Failed to load PDF.";
                } else {
                    pdfLoading.textContent = "Failed to load PDF.";
                }
            }
        }
    }

    async function renderPage(pageNum) {
        console.log("Rendering page:", pageNum);
        const page = await pdfDoc.getPage(pageNum);
        const viewport = page.getViewport({ scale: currentScale });
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");

        canvas.width = viewport.width;
        canvas.height = viewport.height;
        canvas.style.margin = "0 auto 20px";
        canvas.style.display = "block";
        canvas.style.borderRadius = "6px";
        canvas.style.boxShadow = "0 2px 4px rgba(0,0,0,0.15)";
        canvas.style.background = "white";
        canvas.style.opacity = 0;
        canvas.style.transition = "opacity 0.3s ease";

        pdfViewer.appendChild(canvas);

        await page.render({ canvasContext: ctx, viewport }).promise;

        requestAnimationFrame(() => {
            canvas.style.opacity = 1;
        });
    }

    async function renderAllPages() {
        console.log("Rendering all pages...");
        // clear any existing canvases
        pdfViewer.innerHTML = "";
        for (let i = 1; i <= pdfDoc.numPages; i++) {
            await renderPage(i);
        }
        console.log("All pages rendered");
    }

    function downloadCachedPdf() {
        if (!cachedPdfBlob) {
            // fallback to server download
            window.location.href = pdfUrl;
            return;
        }
        const url = URL.createObjectURL(cachedPdfBlob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${reportName}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(()=>URL.revokeObjectURL(url), 10000);
    }

    window.addEventListener("load", () => {
        console.log("Window loaded, calling loadPdf...");
        loadPdf();
    });

    // Download & delete buttons
    const downloadButton = document.getElementById("downloadBtn");
    const deleteButton = document.getElementById("deleteBtn");

    if (downloadButton) {
        downloadButton.addEventListener("click", async () => {
            let reportNameLocal = downloadButton.dataset.report;
            console.log("Download button clicked for report:", reportNameLocal);
            const res = await fetch(`/download_report_files/${reportNameLocal}`);
            if (!res.ok) {
                console.error("Failed to get file list");
                return alert("Failed to get file list");
            }
            const { files } = await res.json();
            for (const file of files) {
                console.log("Downloading file:", file.filename, file.url);
                const response = await fetch(file.url);
                if (!response.ok) continue;
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = file.filename;
                a.click();
                URL.revokeObjectURL(url);
            }
        });
    }

    if (deleteButton) {
        deleteButton.addEventListener("click", () => {
            const reportNameLocal = deleteButton.dataset.report;
            console.log("Delete button clicked for report:", reportNameLocal);
            
            // Use the custom confirm action (UPDATED)
            confirmAction("delete", reportNameLocal, () => deleteReport(reportNameLocal, redirectUrl));
        });
    }
}

// ------------------------------
// Close modal with Escape key
// ------------------------------
document.addEventListener("keydown", (e) => {
    // Check if the Escape key was pressed and the modal is currently visible
    if (e.key === "Escape" && confirmModal.style.display === "flex") {
        // Prevent default browser actions (like scrolling)
        e.preventDefault(); 
        
        // This executes the same logic as hitting "Cancel"
        pendingAction = null;
        confirmModal.style.display = "none";
        
        // Optional: refocus on the delete button or the element that opened the modal
        const deleteButton = document.getElementById("deleteBtn");
        if (deleteButton) deleteButton.focus();
    }
});


initPdfViewer();

document.addEventListener("DOMContentLoaded", function() {

    // --- EXECUTION: This section runs the initial date formatting on page load ---
    
    const elementsToFormat = [
        { id: "dateAdded", label: "Date Added" },
        { id: "dateModified", label: "Last Modified" },
        { id: "lastGenerated", label: "Last Generated" }
    ];

    elementsToFormat.forEach(({ id, label }) => {
        const element = document.getElementById(id);
        if (element) {
            const rawDate = element.dataset.rawDate; 
            // formatFriendlyETDate is accessed from the global scope
            const formattedDate = formatFriendlyETDate(rawDate);
            element.innerHTML = `<strong>${label}: </strong> ${formattedDate}`;
        }
    });
});