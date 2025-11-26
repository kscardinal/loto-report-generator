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
const resendLink = document.getElementById("resendLink");
const resendCountdown = document.getElementById("resendCountdown");
let resendIntervalId = null;
let sendTimestamps = []; // track send times in ms; resets on page reload


email.addEventListener("input", async function() {
    const emailPattern = /^[^\s@]+@[^\s@]+\.[a-zA-Z]{2,}$/;
    
    if (email.value.length === 0) {
        email.classList.remove("error");
        emailCheckMessage.style.display = "none";
        emailCheckMessage.textContent = "❌ Invalid Email Address";
    } else if (emailPattern.test(email.value)) {
        emailCheckMessage.textContent = "";
        emailCheckMessage.style.display = "none";
        email.classList.remove("error");
        sendButton.disabled = false;
        sendButton.style.backgroundColor = "#C32026";
        sendButton.style.cursor = "pointer";
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

code.addEventListener("input", function() {
    codeMessage.style.display = "none";
    code.classList.remove("error");
});


confirmPassword.addEventListener("input", function() {
    passwordMatch()
    validateForm()
});

let codeSent = false; // track whether the backup code has been sent
let verifyCode = false;
let codeAttempts = 0;
let codesSent = 0;

sendButton.addEventListener("click", async function() {
    const emailValue = email.value.trim();
    const codeValue = code.value.trim();
    
    if (!emailValue) {
        alert("Please enter an email.");
        return;
    }

    if (!codeSent) {
        // First press → send backup code
        try {
            const res = await fetch("/send_backup_code", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ email: emailValue }) // Must match FastAPI key
            });

            const data = await res.json();

            if (!res.ok) {
                // Handle different HTTP status codes
                let message = "Something went wrong";
                if (res.status === 400) {
                    // Could be missing email OR no backup code
                    if (data.detail === "Missing email") {
                        message = "Please enter your email";
                    } else if (data.detail === "User has no backup code stored") {
                        message = "This user has no backup code available";
                    } else {
                        message = data.detail;
                    }
                } else if (res.status === 404) {
                    message = "User not found";
                }

                // Update UI
                emailCheckMessage.textContent = "❌ " + message;
                emailCheckMessage.style.display = "block";
                email.classList.add("error");

                return;
            }

            email.disabled = true;
            emailCheckMessage.textContent = "";
            emailCheckMessage.style.display = "none";
            sendButton.textContent = "Verify";
            code.style.display = "block";
            code.required = true;
            codeSent = true; // update state
            codesSent = codesSent + 1;
            sendTimestamps.push(Date.now());

            // Show resend UI and start the first cooldown before allowing resend
            const resendContainer = document.getElementById("resendContainer");
            if (resendContainer) resendContainer.style.display = "block";
            if (codesSent <= 1) {
                // After the initial send, require 15s before the next resend
                startResendCountdown(15);
            } else if (codesSent === 2) {
                // After the second send, require 90s (1.5 minutes) before the third
                startResendCountdown(90);
            } else if (codesSent === 3) {
                // After the second send, require 900s (15 minutes) before the fourth
                startResendCountdown(900);
            } else {
                // Further resends locked out until page reload
                resendLink.classList.add("disabled");
                resendLink.textContent = "Locked out for a while";
                resendLink.style.textDecoration = "none";
            }

            return data;

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
            const res = await fetch("/verify_backup_code", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: emailValue, code: codeValue })
            });

            const data = await res.json();

            if (!res.ok) {
                // Handle different HTTP status codes
                let message = "Something went wrong";
                if (res.status === 400) {
                    // Could be missing email OR no backup code
                    if (data.detail === "Missing email or code") {
                        message = "This user has no backup code available";
                    } else if (data.detail === "No backup code stored for this user") {
                        message = "This user has no backup code available";
                    } else if (data.detail === "Invalid backup code") {
                        message = "Invalid backup code";
                    } else {
                        message = data.detail;
                    }
                } else if (res.status === 404) {
                    message = "User not found";
                }

                // Update UI
                codeMessage.textContent = "❌ " + message;
                codeMessage.style.display = "block";
                code.classList.add("error");

                codeAttempts = codeAttempts + 1;

                return;
            }

            // Get the container element for the resend UI
            const resendContainer = document.getElementById("resendContainer");
            
            // 1. Clear the countdown interval
            if (resendIntervalId) {
                clearInterval(resendIntervalId);
                resendIntervalId = null;
            }

            // 2. Hide the entire container holding the link/countdown
            if (resendContainer) {
                resendContainer.style.display = "none";
            }

            resendLink.style.display = "none";
            resendCountdown.style.display = 'none';
            sendButton.disabled = true;
            sendButton.textContent = "Update Password";
            code.style.display = "none";
            codeMessage.style.display = "none";
            password.style.display = "block";
            confirmPassword.style.display = "block";
            password.required = true;
            confirmPassword.required = true;
            verifyCode = true;

            const response_2 = await fetch("/update-verification-attempts", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({ 
                    email: emailValue, 
                    verification_attempts: codeAttempts 
                })
            });

            return data;

        } catch (err) {
            console.error("Error verifying backup code:", err);
            alert(err.message);
        }
    } else {
        // Third press → update password
        const newPassword = password.value;
        const confirmPasswordValue = confirmPassword.value;

        if (!newPassword || !confirmPasswordValue) {
            alert("Please fill out both password fields.");
            return;
        }

        if (newPassword !== confirmPasswordValue) {
            alert("Passwords do not match.");
            return;
        }

        try {
            const res = await fetch("/reset_password", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: emailValue, new_password: confirmPasswordValue })
            });

            const data = await res.json();

            if (res.ok) {
                window.location.href = "/login";
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
    const passwordValue = password.value;
    const confirmPasswordValue = confirmPassword.value;

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
        sendButton.style.backgroundColor = "#C32026"; // green when active
        sendButton.style.cursor = "pointer";         // change cursor
    } else {
        sendButton.disabled = true;
        sendButton.style.backgroundColor = "#ccc";   // gray when disabled
        sendButton.style.cursor = "not-allowed";     // indicate disabled
    }
}

// Start a countdown (seconds) before enabling the resend link
function startResendCountdown(seconds) {
    // clear any existing interval
    if (resendIntervalId) {
        clearInterval(resendIntervalId);
        resendIntervalId = null;
    }

    const link = resendLink;
    const countdownEl = resendCountdown;
    if (!link || !countdownEl) return;

    link.style.display = 'none';
    link.classList.add('disabled');
    countdownEl.style.display = 'inline';

    let remaining = seconds;
    countdownEl.textContent = `Resend in ${remaining}s`;

    resendIntervalId = setInterval(() => {
        remaining -= 1;
        if (remaining <= 0) {
            clearInterval(resendIntervalId);
            resendIntervalId = null;
            countdownEl.style.display = 'none';
            link.style.display = 'inline';
            link.classList.remove('disabled');
        } else {
            countdownEl.textContent = `Resend in ${remaining}s`;
        }
    }, 1000);
}

// Resend link click handler
    if (resendLink) {
        resendLink.addEventListener('click', async function (e) {
            e.preventDefault();
            if (resendLink.classList.contains('disabled')) return;

            const emailValue = email.value.trim();
            if (!emailValue) {
                return;
            }

            try {
                // Client-side enforces cooldown stages; server may still respond with 429,
                // so handle server-side retry_after if present.
                const res = await fetch('/send_backup_code', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: emailValue })
                });

                if (res.status === 429) {
                    const data = await res.json().catch(()=>({}));
                    const retry = data.retry_after || 900; // fallback to longest cooldown
                    startResendCountdown(retry);
                    return;
                }

                if (!res.ok) {
                    const data = await res.json().catch(()=>({}));
                    alert(data.detail || data.message || 'Failed to resend code');
                    return;
                }

                // Success: record timestamp and advance stage
                sendTimestamps.push(Date.now());
                codesSent = codesSent + 1;

                // After second send (codesSent===2) start the shorter 90s cooldown,
                // after third send lock out.
                if (sendTimestamps.length === 1) {
                    // shouldn't happen — initial send already recorded, but be safe
                    startResendCountdown(15);
                } else if (sendTimestamps.length === 2) {
                    startResendCountdown(90);
                } else if (sendTimestamps.length === 3) {
                    startResendCountdown(900);
                } else {
                    // Lock out UI until reload
                    clearInterval(resendIntervalId);
                    resendIntervalId = null;
                    resendCountdown.style.display = 'none';
                    resendLink.style.display = 'inline';
                    resendLink.classList.add('disabled');
                    resendLink.textContent = 'Locked out for a while';
                }

                return;
            } catch (err) {
                // Non-fatal client-side error — show a simple alert
                alert('Error resending backup code. Please try again later.');
            }
        });
    }