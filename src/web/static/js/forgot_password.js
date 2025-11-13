const email = document.getElementById("emailInput");
const emailCheckMessage = document.getElementById("emailCheck");

const code = document.getElementById("codeInput");
const codeMessage = document.getElementById("codeCheck");

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

const sendButton = document.getElementById("sendButton")


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
            emailCheckMessage.textContent = "";
            emailCheckMessage.style.display = "none";
            email.classList.remove("error");
            sendButton.disabled = false;
            sendButton.style.backgroundColor = "#4CAF50";
            sendButton.style.cursor = "pointer";
        } else {
            email.classList.add("error");
            emailCheckMessage.style.display = "block";
            emailCheckMessage.textContent = "❌ Email doesn't exist";
            sendButton.disabled = true;
            sendButton.style.backgroundColor = "#ccc";
            sendButton.style.cursor = "not-allowed"; 
        }
    } else {
        email.classList.add("error");
        emailCheckMessage.style.display = "block";
        emailCheckMessage.textContent = "❌ Invalid Email Address";
    }
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

let codeSent = false; // track whether the backup code has been sent
let verifyCode = false;
let codeAttempts = 0;

sendButton.addEventListener("click", async function() {
    const emailValue = email.value.trim();
    const codeValue = code.value.trim(); // get the code input
    if (!emailValue) {
        alert("Please enter an email.");
        return;
    }

    if (!codeSent) {
        // First press → send backup code
        try {
            const exists = await checkAvailabilityBool("email", emailValue);

            if (!exists) {
                alert("This email is not registered in our system.");
                return;
            }

            const response = await fetch("http://127.0.0.1:5000/send-backup-code", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: emailValue })
            });

            const result = await response.json();

            if (result.success) {
                email.disabled = true;
                emailMessage.textContent = "";
                sendButton.textContent = "Verify";
                code.style.display = "block";
                code.required = true;
                codeSent = true; // update state
            } else {
                alert(result.message);
            }
        } catch (err) {
            console.error("Error sending backup code:", err);
            alert("Something went wrong while sending the email.");
        }

    } else if (!verifyCode) {
        // Second press → verify the backup code
        if (!codeValue) {
            alert("Please enter the backup code.");
            return;
        }

        try {
            const response = await fetch("http://127.0.0.1:5000/verify-backup-code", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: emailValue, backup_code: codeValue })
            });

            const result = await response.json();

            if (result.success) {
                sendButton.disabled = true;
                sendButton.textContent = "Update Password"
                code.style.display = "none";
                password.style.display = "block";
                confirmPassword.style.display = "block";
                password.required = true;
                confirmPassword.required = true;
                verifyCode = true;
            } else {
                codeAttempts = codeAttempts + 1;
                console.log(codeAttempts)
                alert("Invalid backup code, please try again.");
            }
        } catch (err) {
            console.error("Error verifying backup code:", err);
            alert("Something went wrong while verifying the code.");
        }
    } else {
        // Third press → update password
        newPassword = password.value;
        confirmPasswordValue = confirmPassword.value;
        if (!newPassword || !confirmPasswordValue) {
            alert("Please fill out both password fields.");
            return;
        }

        if (newPassword !== confirmPasswordValue) {
            alert("Passwords do not match.");
            return;
        }

        try {
            const response = await fetch("http://127.0.0.1:5000/update-password", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: emailValue, new_password: newPassword })
            });

            const result = await response.json();

            if (result.success) {

                try {
                    const response = await fetch("http://127.0.0.1:5000/update-verification-attempts", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        credentials: "include", // send cookies if needed
                        body: JSON.stringify({
                            email: emailValue,             // the user's email
                            verification_attempts: codeAttempts      
                        })
                    });

                    const data = await response.json();
                } catch (err) {
                    console.error("Failed to reset verification_attempts:", err);
                }


                console.log("Redirecting…");
                window.location.href = "Login.html";
            } else {
                alert(result.message || "Failed to update password.");
            }
        } catch (err) {
            console.error("Error updating password:", err);
            alert("Something went wrong while updating the password.");
        }
    }
});

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

async function validateForm() {
    const emailValue = email.value;
    const passwordValue = password.value;
    const confirmPasswordValue = confirmPassword.value;

    const emailPattern = /^[^\s@]+@[^\s@]+\.[a-zA-Z]{2,}$/;
    const forbiddenPattern = /[\s\t\n\r\"']/;
    const lowercasePattern = /[a-z]/;
    const uppercasePattern = /[A-Z]/;
    const numberPattern = /[0-9]/;
    const specialPattern = /[!@#$%^&*()_\-+=\[\]{}|;:'\",.<>?/]/;
    const minPasswordLength = 12;

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
    const isValid = passwordIsValid && passwordsMatch;

    if (isValid) {
        sendButton.disabled = false;
        sendButton.style.backgroundColor = "#4CAF50"; // green when active
        sendButton.style.cursor = "pointer";         // change cursor
    } else {
        sendButton.disabled = true;
        sendButton.style.backgroundColor = "#ccc";   // gray when disabled
        sendButton.style.cursor = "not-allowed";     // indicate disabled
    }
}