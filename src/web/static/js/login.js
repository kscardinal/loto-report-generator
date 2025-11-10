const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");

const emailCheck = document.getElementById("emailCheck");
const passwordCheck = document.getElementById("passwordCheck");

let login_attempts = 0;

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

            // Example call when password is wrong
            await fetch("/update-login-attempts", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                credentials: "include",
                body: JSON.stringify({ login_attempts: login_attempts })
            });

            window.location.href = "/pdf_list";
        } else if (response.status === 404) {
            // User not found
            passwordCheck.style.display = "none";
            emailCheck.textContent = "❌ User does not exist";
            emailCheck.style.display = "block";
        } else if (response.status === 401) {
            // Wrong password
            emailCheck.style.display = "none";
            passwordCheck.textContent = "❌ Wrong password";
            passwordCheck.style.display = "block";
            login_attempts += 1;
            console.log("Login attempts:", login_attempts);
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
});

// Hide alert when user edits the password
passwordInput.addEventListener("input", () => {
    passwordCheck.style.display = "none";
});