// Action Buttons
const downloadButton = document.getElementById("downloadBtn") as HTMLButtonElement | null;
const generateButton = document.getElementById("generateBtn") as HTMLButtonElement | null;

// Track the validity of each monitored input field by input ID
const fieldValidity: Record<string, boolean> = {
  procedure_number: true,
  revision: true,
  origin: true,
  isolation_points: true
};

let downloadable = false; // overall downloadable flag

// Enables/Disables a single button based on downloadable state
function updateButton(buttonElement: HTMLButtonElement | null): void {
  if (!buttonElement) return;
  if (downloadable) {
    buttonElement.disabled = false;
    buttonElement.style.cursor = "pointer";
    buttonElement.classList.remove("button-disabled");
  } else {
    buttonElement.disabled = true;
    buttonElement.style.cursor = "not-allowed";
    buttonElement.classList.add("button-disabled");
  }
}

// Enables/Disables the download and generate buttons
function updateButtons(): void {
  updateButton(downloadButton);
  updateButton(generateButton);
}

// Adds input listener for number-only validation, updates validity state and buttons
function checkOnlyNumber(inputId: string, validityObj: Record<string, boolean>): void {
  const inputElement = document.getElementById(inputId) as HTMLInputElement | null;
  const labelElement = document.getElementById(inputId + "_label") as HTMLElement | null;

  if (!inputElement || !labelElement) return;

  inputElement.addEventListener("input", () => {
    const val = inputElement.value;
    const numberOnlyRegex = /^\d+$/;

    if (val.length > 0) {
      const passed = numberOnlyRegex.test(val);

      if (!passed) {
        labelElement.style.display = "block";
        labelElement.textContent = " ❌ Must only be a number";
        inputElement.classList.add("error");
        validityObj[inputId] = false;
      } else {
        labelElement.style.display = "none";
        inputElement.classList.remove("error");
        validityObj[inputId] = true;
      }
    } else {
      labelElement.style.display = "none";
      inputElement.classList.remove("error");
      // Adjust validity on empty input as per your requirements
      validityObj[inputId] = true;
    }

    // Update overall downloadable state: all fields must be valid
    downloadable = Object.keys(validityObj).every(key => validityObj[key]);
    updateButtons();
  });
}

// Initialize validation listeners on all desired fields
checkOnlyNumber("procedure_number", fieldValidity);
checkOnlyNumber("revision", fieldValidity);
checkOnlyNumber("origin", fieldValidity);
checkOnlyNumber("isolation_points", fieldValidity);

// Initially update buttons disabled state according to initial validity
downloadable = Object.keys(fieldValidity).every(key => fieldValidity[key]);
updateButtons();

// Optional: add click listeners on buttons with proper type checks
downloadButton?.addEventListener("click", () => {
  console.log("Download Button Pressed!");
});

generateButton?.addEventListener("click", () => {
  console.log("Generate Button Pressed!");
});
