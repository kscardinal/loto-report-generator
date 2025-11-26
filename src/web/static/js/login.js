const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");

const emailCheck = document.getElementById("emailCheck");
const passwordCheck = document.getElementById("passwordCheck");
const activationCheck = document.getElementById("activationCheck");

// REMOVED: let current_login_attempts = 0; // The counter is now strictly server-side

document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const usernameOrEmail = usernameInput.value;
    const password = passwordInput.value;

    try {
        const response = await fetch("/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username_or_email: usernameOrEmail, password }),
            credentials: "include"
        });

        const data = await response.json(); // Fetch the JSON data once

        if (response.status === 200) {
            // Success
            emailCheck.style.display = "none";
            passwordCheck.style.display = "none";
            
            const returnUrl = data.return_url || "/pdf_list";
            window.location.href = returnUrl;
        
        } else if (response.status === 429) {
            // 🔒 Account Locked Out - Display the exact server message with remaining time
            emailCheck.style.display = "none";
            passwordCheck.style.display = "block";
            
            // This line uses the 'data.message' which contains the time frame
            passwordCheck.textContent = `❌ ${data.message}`; 
            
            passwordInput.blur();
        
        } else if (response.status === 401) {
            // Wrong password (The server will handle the generic message)
            emailCheck.style.display = "none";
            passwordCheck.textContent = "❌ Wrong password";
            passwordCheck.style.display = "block";
            passwordInput.focus();
            passwordInput.select();
        
        } else if (response.status === 403) {
            // Account not activated
            emailCheck.style.display = "none";
            passwordCheck.style.display = "none";
            activationCheck.textContent = "❌ Your account has not been activated yet";
            activationCheck.style.display = "block";
            passwordInput.blur();
        
        } else {
            // Handle other unexpected errors
            emailCheck.style.display = "none";
            passwordCheck.style.display = "none";
            activationCheck.style.display = "none";
        }
    } catch (err) {
        console.error("Login request failed:", err);
        emailCheck.style.display = "none";
        passwordCheck.style.display = "none";
    }
});


// Hide alert when user edits the username/email
usernameInput.addEventListener("input", () => {
    emailCheck.style.display = "none";
    activationCheck.style.display = "none";
});

// Hide alert when user edits the password
passwordInput.addEventListener("input", () => {
    passwordCheck.style.display = "none";
    activationCheck.style.display = "none";
});
