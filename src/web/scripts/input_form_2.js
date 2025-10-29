// Action Buttons
const downloadButton = document.getElementById("downloadBtn");
const generateButton = document.getElementById("generateBtn");

// Track the validity of each monitored input field
let fieldValidity = {
  procedure_number: true,
  revision: true,
  origin: true,
  isolation_points: true,
  machine_image: true
};

let downloadable = false; // overall downloadable flag

// Enables/Disables a single button based on downloadable state
function updateButton(buttonElement) {
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
function updateButtons() {
  updateButton(downloadButton);
  updateButton(generateButton);
}

function isImageFile(file) {
  const validTypes = ["image/jpg", "image/jpeg", "image/png"];
  const validExt = /\.(jpg|jpeg|png)$/i;

  // Extract extension (lowercase, without the dot)
  const match = file.name.toLowerCase().match(/\.([a-z0-9]+)$/);
  const extension = match ? match[1] : null;

  const isValid = validTypes.includes(file.type) && validExt.test(file.name);

  return { isValid, extension };
}


// Adds input listener for number-only validation, updates validity state and buttons
function checkOnlyNumber(inputId, validityObj) {
  const inputElement = document.getElementById(inputId);
  const labelElement = document.getElementById(inputId + "_label");

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
      // Consider empty input as valid or adjust this line depending on your requirements
      validityObj[inputId] = true; 
    }

    // Update overall downloadable state: all fields must be valid
    downloadable = Object.values(validityObj).every(Boolean);
    updateButtons();
  });
}

function checkOnlyImage(inputId, validityObj) {
    const inputElement = document.getElementById(inputId);
    const labelElement = document.getElementById(inputId + "_label");

    if (!inputElement || !labelElement) return;

        inputElement.addEventListener("change", () => {
            const file = inputElement.files[0];
            if (!file) return;

            const { isValid, extension } = isImageFile(file);

            if (!isValid) {
                labelElement.style.display = "block";
                labelElement.textContent = " ❌ " + extension + " is not supported. Can only be jpg, jpeg or png.";
                inputElement.classList.add("error");
                validityObj[inputId] = false;
            } else {
                labelElement.style.display = "none";
                inputElement.classList.remove("error");
                validityObj[inputId] = true;
            }

            // Update overall downloadable state: all fields must be valid
            downloadable = Object.values(validityObj).every(Boolean);
            updateButtons();
        });
}


// Set up validation listeners on all desired fields
checkOnlyNumber("procedure_number", fieldValidity);
checkOnlyNumber("revision", fieldValidity);
checkOnlyNumber("origin", fieldValidity);
checkOnlyNumber("isolation_points", fieldValidity);
checkOnlyImage("machine_image", fieldValidity);

// Initially update buttons disabled state according to initial validity
downloadable = Object.values(fieldValidity).every(Boolean);
updateButtons();



downloadButton.addEventListener("click", function() {
    console.log("Download Button Pressed!")
});

generateButton.addEventListener("click", function() {
    console.log("Generate Button Pressed!")
});
