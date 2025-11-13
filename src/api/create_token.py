import jwt
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

VALID_ROLES = {"user", "admin", "owner"}

def get_valid_input(prompt, default, validate_func, error_msg):
    for _ in range(3):  # maximum 3 attempts
        value = input(f"{prompt} [{default}]: ").strip() or default
        if validate_func(value):
            return value
        else:
            print(error_msg)
    print("Too many invalid attempts. Exiting.")
    exit(1)

def validate_role(role):
    return role.lower() in VALID_ROLES

def validate_days(days):
    try:
        return int(days) > 0
    except ValueError:
        return False

def generate_custom_jwt():
    print("=== JWT Generator ===")

    token_name = input("Enter a name for this token [default_token]: ").strip() or "default_token"
    role = get_valid_input(
        "Enter role for this token (user/admin/owner)",
        "user",
        validate_role,
        "Invalid role! Must be one of: user, admin, owner.",
    ).lower()
    days_raw = get_valid_input(
        "Enter expiration in days (integer)",
        "7",
        validate_days,
        "Invalid value! Must be a positive integer.",
    )
    days = int(days_raw)

    payload = {
        "sub": token_name,
        "role": role,
        "exp": datetime.now() + timedelta(days=days)
    }

    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        print("Error: SECRET_KEY environment variable not set!")
        exit(1)

    token = jwt.encode(payload, secret_key, algorithm="HS256")
    print("\n=== Generated JWT ===")
    print(token)
    print("====================\n")
    print(f"Copy this token into your .env as:\n{token_name.upper()}_JWT={token}")

if __name__ == "__main__":
    generate_custom_jwt()
