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

async function initPdfViewer() {
	console.log("Initializing PDF viewer...");

	// Ensure pdfjsLib is available. Some CDN builds may not expose a global; use a UMD build from cdnjs as a fallback.
	if (typeof window.pdfjsLib === 'undefined') {
		console.warn('pdfjsLib not found; loading fallback UMD build from cdnjs...');
		// Load a stable UMD build that exposes pdfjsLib
		await loadScript('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.14.305/pdf.min.js');
		// set worker to the matching cdn version
		window.pdfjsLib = window.pdfjsLib || window.pdfjsDistPdfjs || window['pdfjs-dist/build/pdf'];
		if (!window.pdfjsLib) {
			console.error('Fallback PDF.js did not expose pdfjsLib');
			return;
		}
		window.pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.14.305/pdf.worker.min.js';
	} else {
		// If already present, ensure workerSrc is set (use a reliable CDN path)
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
		// preserving the spinner structure.
		const loadingText = pdfLoading ? pdfLoading.querySelector('p') : null;

		// Update the status text at the beginning of the load
		if (loadingText) loadingText.textContent = "Loading PDF data...";
		
		try {
			const resp = await fetch(pdfUrl, { credentials: 'include' });
			if (!resp.ok) {
				const txt = await resp.text().catch(() => null);
				throw new Error(txt || `HTTP ${resp.status}`);
			}

			const blob = await resp.blob();
			cachedPdfBlob = blob;

			const arrayBuffer = await blob.arrayBuffer();

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
				downloadAnchor.setAttribute('aria-disabled', 'false');
			}

		} catch (err) {
			console.error("Error loading PDF:", err);
			
			// Handle error: remove the spinner and display the error message
			if (pdfLoading) {
				const spinner = pdfLoading.querySelector('.spinner');
				if (spinner) spinner.remove();

				if (loadingText) {
					loadingText.textContent = "Failed to load PDF.";
				} else {
					// Fallback in case loadingText couldn't be found/defined
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