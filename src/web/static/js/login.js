const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");

const emailCheck = document.getElementById("emailCheck");
const passwordCheck = document.getElementById("passwordCheck");
const activationCheck = document.getElementById("activationCheck");

let current_login_attempts = 0;

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

        if (response.status === 200) {
            // Success
            emailCheck.style.display = "none";
            passwordCheck.style.display = "none";
            const response_2 = await fetch("/update-login-attempts", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({ 
                    username: usernameInput.value.toLowerCase(), 
                    login_attempts: current_login_attempts 
                })
            });
            const data = await response.json();
            const returnUrl = data.return_url || "/pdf_list";
            window.location.href = returnUrl;
        } else if (response.status === 404) {
            // User not found
            passwordCheck.style.display = "none";
            emailCheck.textContent = "❌ User does not exist";
            emailCheck.style.display = "block";
            usernameInput.focus();
            usernameInput.select();
        } else if (response.status === 401) {
            // Wrong password
            emailCheck.style.display = "none";
            passwordCheck.textContent = "❌ Wrong password";
            passwordCheck.style.display = "block";
            passwordInput.focus();
            passwordInput.select();
            current_login_attempts += 1;
            const response_2 = await fetch("/update-login-attempts", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({ 
                    username: usernameInput.value.toLowerCase(), 
                    login_attempts: current_login_attempts 
                })
            });
        } else if (response.status === 403) {
            // Account not activated
            emailCheck.style.display = "none";
            passwordCheck.style.display = "none";
            activationCheck.textContent = "❌ Your account has not been activated yet";
            activationCheck.style.display = "block";
            passwordInput.blur();
            current_login_attempts += 1;
            const response_2 = await fetch("/update-login-attempts", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({ 
                    username: usernameInput.value.toLowerCase(), 
                    login_attempts: current_login_attempts 
                })
            });
        } else {
            emailCheck.style.display = "none";
            passwordCheck.style.display = "none";
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