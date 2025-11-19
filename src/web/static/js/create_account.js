function hasSequential(str) {
    const s = str.toLowerCase();
    let count = 0;

    for (let i = 0; i < s.length - 2; i++) {
        const a = s.charCodeAt(i);
        const b = s.charCodeAt(i + 1);
        const c = s.charCodeAt(i + 2);

        // ascending sequence
        if (b === a + 1 && c === b + 1) {
            count++;
            i += 2; // skip ahead so overlapping sequences counted separately
        }
    }
    return count >= 2; // at least 2 sequences of length 3+
}

function getGradientColor(percent) {
    let r, g, b = 0;

    if (percent <= 50) {
        // Red to Yellow-ish
        r = 255;
        g = Math.round(220 * (percent / 50));  // max green 220 instead of 255
    } else {
        // Yellow-ish to Darker Green
        g = 180 + Math.round(40 * ((100 - percent) / 50)); // g goes 220->180
        r = Math.round(255 * ((100 - percent) / 50));       // r goes 255->0
    }

    return `rgb(${r},${g},${b})`;
}

const form = document.getElementById("signupForm")
const firstName = document.getElementById("firstNameInput")
const lastName = document.getElementById("lastNameInput")
const email = document.getElementById("emailInput")
const emailCheckMessage = document.getElementById("emailCheck")
const usernameCheckMessage = document.getElementById("usernameCheck")
const username = document.getElementById('username')
const password = document.getElementById('passwordInput')
const confirmPassword = document.getElementById('confirmPassword')
const errorMessage = document.getElementById("errorMessage");
const passwordCheckLength = document.getElementById("passwordCheck-Length");
const passwordCheckForbidden = document.getElementById("passwordCheck-Forbidden");
const passwordCheckUppercase = document.getElementById("passwordCheck-Uppercase");
const passwordCheckLowercase = document.getElementById("passwordCheck-Lowercase");
const passwordCheckNumber = document.getElementById("passwordCheck-Number");
const passwordCheckSpecial = document.getElementById("passwordCheck-Special");
const passwordCheckConfirm = document.getElementById("passwordCheck-Confirm");
const passwordCheckWord = document.getElementById("passwordCheck-Word");
const passwordCheckRepeat = document.getElementById("passwordCheck-Repeat");
const passwordCheckSequential = document.getElementById("passwordCheck-Sequential");
const entropyContainer = document.getElementById("entropy-Container")
const entropyBar = document.getElementById("entropy-bar")
const entropyWords = document.getElementById("entropy-words")
const createButton = document.getElementById("create-Button")

async function validateForm() {
    const firstNameValue = firstName.value;
    const lastNameValue = lastName.value;
    const emailValue = email.value;
    const usernameValue = username.value;
    const passwordValue = password.value;
    const confirmPasswordValue = confirmPassword.value;

    const emailPattern = /^[^\s@]+@[^\s@]+\.[a-zA-Z]{2,}$/;
    const forbiddenPattern = /[\s\t\n\r\"']/;
    const lowercasePattern = /[a-z]/;
    const uppercasePattern = /[A-Z]/;
    const numberPattern = /[0-9]/;
    const specialPattern = /[!@#$%^&*()_\-+=\[\]{}|;:'\",.<>?/]/;
    const minPasswordLength = 12;

    // Name check
    const firstNameValid = firstNameValue.length > 0;
    const lastNameValid = lastNameValue.length > 0;

    // Username check
    const usernameValid = usernameValue.length > 0 && !forbiddenPattern.test(usernameValue);

    // Email check
    const emailIsValid = emailPattern.test(emailValue);

    // Password checks
    const passwordHasNoForbidden = !forbiddenPattern.test(passwordValue);
    const passwordHasLowercase = lowercasePattern.test(passwordValue);
    const passwordHasUppercase = uppercasePattern.test(passwordValue);
    const passwordHasNumber = numberPattern.test(passwordValue);
    const passwordHasSpecial = specialPattern.test(passwordValue);
    const passwordHasMinLength = passwordValue.length >= minPasswordLength;

    // Password overall validity
    const passwordIsValid = passwordHasNoForbidden &&
                            passwordHasLowercase &&
                            passwordHasUppercase &&
                            passwordHasNumber &&
                            passwordHasSpecial &&
                            passwordHasMinLength;

    // Confirm password matches
    const passwordsMatch = passwordValue === confirmPasswordValue;

    // Final result: all conditions met
    const isValid = emailIsValid && passwordIsValid && passwordsMatch && firstNameValid && lastNameValid && usernameValid && !email.classList.contains("error") && !username.classList.contains("error");

    if (isValid) {
        createButton.disabled = false;
        createButton.style.backgroundColor = "#C32026"; // green when active
        createButton.style.cursor = "pointer";         // change cursor
    } else {
        createButton.disabled = true;
        createButton.style.backgroundColor = "#ccc";   // gray when disabled
        createButton.style.cursor = "not-allowed";     // indicate disabled
    }
}

function passwordMatch() {
    if (confirmPassword.value.length === 0) {
        passwordCheckConfirm.style.display = "none";
        passwordCheckConfirm.textContent = "❌ Password must match";
        confirmPassword.classList.remove("error");
    } else if (confirmPassword.value === password.value) {
        passwordCheckConfirm.style.display = "block";
        passwordCheckConfirm.textContent = "✔️ Password must match";
        confirmPassword.classList.remove("error");
    } else {
        passwordCheckConfirm.style.display = "block";
        passwordCheckConfirm.textContent = "❌ Password must match";
        confirmPassword.classList.add("error");
    }
    validateForm()
}

firstName.addEventListener("input", function() {
    const val = firstName.value;
    validateForm()
});

lastName.addEventListener("input", function() {    
    const val = lastName.value;
    validateForm()
});

email.addEventListener("input", async function() {
    const emailPattern = /^[^\s@]+@[^\s@]+\.[a-zA-Z]{2,}$/;
    
    if (email.value.length === 0) {
        email.classList.remove("error");
        emailCheckMessage.style.display = "none";
        emailCheckMessage.textContent = "❌ Invalid Email Address";
    } else if (emailPattern.test(email.value)) {
        const response = await fetch(`/check-username-email?email=${encodeURIComponent(email.value)}`);
        const result = await response.json();
        if (result.exists) {
            emailCheckMessage.textContent = "❌ Email already in use";
            email.classList.add("error");
        } else {
            email.classList.remove("error");
            emailCheckMessage.style.display = "block";
            emailCheckMessage.textContent = "✔️ Valid Email Address";
        }
    } else {
        email.classList.add("error");
        emailCheckMessage.style.display = "block";
        emailCheckMessage.textContent = "❌ Invalid Email Address";
    }
    validateForm()
});

username.addEventListener("input", async function() {
    const val = username.value;

        // ====== Patterns ======
    const forbiddenPattern = /[\s\t\n\r\"']/;

    if (val.length === 0 ) {
        usernameCheckMessage.style.display = "none";
        usernameCheckMessage.textContent = "❌ Invalid Username";
        username.classList.remove("error");
    } else if (forbiddenPattern.test(val)) {
        usernameCheckMessage.style.display = "block";
        usernameCheckMessage.textContent = "❌ Invalid Username";
        username.classList.add("error");
    } else {
        const response = await fetch(`/check-username-email?username=${encodeURIComponent(val)}`);
        const result = await response.json();
        if (result.exists) {
            usernameCheckMessage.textContent = "❌ Username already taken";
            username.classList.add("error");
        } else {
            usernameCheckMessage.style.display = "block";
            usernameCheckMessage.textContent = "✔️ Valid Username";
            username.classList.remove("error");
        }
    }
    validateForm();
});

password.addEventListener("input", function () {
    const val = password.value;

    // ====== Patterns ======
    const forbiddenPattern = /[\s\t\n\r\"']/;
    const uppercasePattern = /[A-Z]/;
    const lowercasePattern = /[a-z]/;
    const numberPattern = /[0-9]/;
    const specialPattern = /[!@#$%^&*()_\-+=\[\]{}|;:'",.<>?/]/;
    const minPasswordLength = 12;

    // ====== Length check ======
    if (val.length === 0) {
        passwordCheckLength.style.display = "none";
        passwordCheckLength.textContent = "❌ Password must be 12 characters minimum";
    } else if (val.length < minPasswordLength) {
        passwordCheckLength.style.display = "block";
        passwordCheckLength.textContent = "❌ Password must be 12 characters minimum";
    } else {
        passwordCheckLength.style.display = "block";
        passwordCheckLength.textContent = "✔️ Password must be 12 characters minimum";
    }

    // ====== Forbidden chars check ======
    if (val.length === 0) {
        passwordCheckForbidden.style.display = "none";
    } else if (forbiddenPattern.test(val)) {
        passwordCheckForbidden.style.display = "block";
        passwordCheckForbidden.textContent = "❌ Password can't contain prohibited items";
    } else {
        passwordCheckForbidden.style.display = "block";
        passwordCheckForbidden.textContent = "✔️ Password can't contain prohibited items";
    }

    // ====== Uppercase ======
    if (val.length === 0) {
        passwordCheckUppercase.style.display = "none";
    } else if (!uppercasePattern.test(val)) {
        passwordCheckUppercase.style.display = "block";
        passwordCheckUppercase.textContent = "❌ Password must contain an uppercase letter";
    } else {
        passwordCheckUppercase.style.display = "block";
        passwordCheckUppercase.textContent = "✔️ Password must contain an uppercase letter";
    }

    // ====== Lowercase ======
    if (val.length === 0) {
        passwordCheckLowercase.style.display = "none";
    } else if (!lowercasePattern.test(val)) {
        passwordCheckLowercase.style.display = "block";
        passwordCheckLowercase.textContent = "❌ Password must contain a lowercase letter";
    } else {
        passwordCheckLowercase.style.display = "block";
        passwordCheckLowercase.textContent = "✔️ Password must contain a lowercase letter";
    }

    // ====== Number ======
    if (val.length === 0) {
        passwordCheckNumber.style.display = "none";
    } else if (!numberPattern.test(val)) {
        passwordCheckNumber.style.display = "block";
        passwordCheckNumber.textContent = "❌ Password must contain a number";
    } else {
        passwordCheckNumber.style.display = "block";
        passwordCheckNumber.textContent = "✔️ Password must contain a number";
    }

    // ====== Special ======
    if (val.length === 0) {
        passwordCheckSpecial.style.display = "none";
    } else if (!specialPattern.test(val)) {
        passwordCheckSpecial.style.display = "block";
        passwordCheckSpecial.textContent = "❌ Password must contain a special character";
    } else {
        passwordCheckSpecial.style.display = "block";
        passwordCheckSpecial.textContent = "✔️ Password must contain a special character";
    }

    // ====== Entropy calculation ======
    let characterPool = 0;
    if (uppercasePattern.test(val)) characterPool += 26;
    if (lowercasePattern.test(val)) characterPool += 26;
    if (numberPattern.test(val)) characterPool += 10;
    if (specialPattern.test(val)) characterPool += 33;

    let entropy = val.length * Math.log2(characterPool || 1); // avoid log2(0)
    let entropyPercentage = Math.min((entropy / 80) * 100, 100);

    // ====== Show/hide entropy container ======
    entropyContainer.style.display = val.length > 0 ? "block" : "none";

    if (entropy <= 28) {
        entropyWords.textContent = "Very Weak";
    } else if (entropy <= 36) {
        entropyWords.textContent = "Weak";
    } else if (entropy <= 60) {
        entropyWords.textContent = "Normal";
    } else if (entropy <= 80) {
        entropyWords.textContent = "Strong";
    } else {
        entropyWords.textContent = "Very Strong";
    }

    entropyBar.style.width = entropyPercentage + "%";
    entropyBar.style.backgroundColor = getGradientColor(entropyPercentage);

    // ====== Repeating sequence check (3+ chars repeating at least once) ======
    const repeatPattern = /(...).*?\1/; // any 3 characters repeated later
    const singleRepeatPattern = /(.)\1{3,}/i; // same character repeated 5 or more times, case-insensitive

    if (repeatPattern.test(val)) {
        passwordCheckRepeat.style.display = "block";
        passwordCheckRepeat.textContent = "⚠️ Warning: password contains repeated sequences";
    } else if (singleRepeatPattern.test(val)) {
        passwordCheckRepeat.style.display = "block";
        passwordCheckRepeat.textContent = "⚠️ Warning: password contains repeated characters";
    } else {
        passwordCheckRepeat.style.display = "none";
    }

    // ====== Sequential characters check (3+ increasing letters or numbers, at least twice) ======
    if (hasSequential(val)) {
        passwordCheckSequential.style.display = "block";
    } else if (!repeatPattern.test(val)) {
        // only hide if no repeats either
        passwordCheckSequential.style.display = "none";
    }
    passwordMatch();
    validateForm()
});


confirmPassword.addEventListener("input", function() {
    passwordMatch()
    validateForm()
});

document.getElementById("signupForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const loadingSpinner = document.getElementById("loadingSpinner");
    const submitButton = document.getElementById("create-Button");

    // Show spinner and disable button
    loadingSpinner.style.display = "flex"; // CHANGE: Use flex to show it
    submitButton.disabled = true;
    submitButton.textContent = "Creating..."; // Leave this text for the button if you want it to change

    // --- NEW: Update the spinner text itself ---
    loadingSpinner.querySelector('span').textContent = "Creating Account...";
    // ---

    const formData = new FormData(e.target);

    try {
        const response = await fetch("/create_account", {
            method: "POST",
            body: formData,
        });

        if (response.redirected) {
            window.location.href = response.url;
        } else {
            const text = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(text, "text/html");
            const errorMessageEl = doc.getElementById("errorMessage");
            if (errorMessageEl) {
                document.getElementById("errorMessage").textContent = errorMessageEl.textContent;
                document.getElementById("errorMessage").style.display = "block";
            } else {
                alert("Account creation failed. Please try again.");
            }
            // Hide spinner & re-enable button on error
            loadingSpinner.style.display = "none";
            submitButton.disabled = false;
            submitButton.textContent = "Create Account";
        }
    } catch (error) {
        console.error("Error submitting form: ", error);
        alert("Failed to create account due to network error.");
        loadingSpinner.style.display = "none";
        submitButton.disabled = false;
        submitButton.textContent = "Create Account";
    }
});
