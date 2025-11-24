# -----------------------------
# Import setup
# -----------------------------
import os
import pytest
import requests

# Assuming your FastAPI application defines the necessary functions
from ..api.auth_utils import create_access_token 

# -----------------------------
# Server setup
# -----------------------------
TEST_SERVER = "http://localhost:8100"

# Skip tests if no server or requests not available
if not TEST_SERVER or not requests:
    reason = (f"Skipping tests: TEST_HOST (or SERVER_IP) not configured or 'requests' not available ")
    pytest.skip(reason, allow_module_level=True)

# -----------------------------
# JWT setup (Owner, Admin, Unauthorized)
# -----------------------------

# Owner User (Highest Role, should pass all admin checks)
OWNER_USERNAME = "owner_test"
OWNER_TOKEN = create_access_token({"sub": OWNER_USERNAME, "role": "owner"})
OWNER_HEADERS = {"Authorization": f"Bearer {OWNER_TOKEN}"}

# Admin User (Authorized, should pass all admin checks)
ADMIN_USERNAME = "admin_test"
ADMIN_TOKEN = create_access_token({"sub": ADMIN_USERNAME, "role": "admin"})
ADMIN_HEADERS = {"Authorization": f"Bearer {ADMIN_TOKEN}"}

# Standard User (Unauthorized, should fail admin checks)
USER_USERNAME = "user_test"
USER_TOKEN = create_access_token({"sub": USER_USERNAME, "role": "user"})
USER_HEADERS = {"Authorization": f"Bearer {USER_TOKEN}"}

# -----------------------------
# TESTS
# -----------------------------

def test_login_page_access(test_environment):
    """
    Tests that the public /login page is accessible and returns HTML.
    Expected: ✅ PASS (200 OK)
    """
    
    print("\n\n🌐 Starting Test: /login page access")
    url = f"{TEST_SERVER}/login"
    print(f"➡️  Requesting: {url} (Expected 200 OK)")
    
    # --- Request ---
    resp = requests.get(url, timeout=5)
    
    print(f"⬇️  Response code: {resp.status_code}")
    
    # --- Assertions ---
    assert resp.status_code == 200, f"❌ Expected 200 from {url}, got {resp.status_code}"
    
    # Check that it returned HTML (confirming it's not an API route)
    assert "text/html" in resp.headers.get("Content-Type", ""), f"❌ Expected Content-Type 'text/html', got {resp.headers.get('Content-Type')}"

    print("✅ /login page access check passed\n")


def test_create_account_page_access(test_environment):
    """
    Tests that the public /create_account page is accessible and returns HTML.
    Expected: ✅ PASS (200 OK)
    """
    
    print("\n\n🌐 Starting Test: /create_account page access")
    url = f"{TEST_SERVER}/create_account"
    print(f"➡️  Requesting: {url} (Expected 200 OK)")
    
    # --- Request ---
    resp = requests.get(url, timeout=5)
    
    print(f"⬇️  Response code: {resp.status_code}")
    
    # --- Assertions ---
    assert resp.status_code == 200, f"❌ Expected 200 from {url}, got {resp.status_code}"
    
    # Check that it returned HTML
    assert "text/html" in resp.headers.get("Content-Type", ""), f"❌ Expected Content-Type 'text/html', got {resp.headers.get('Content-Type')}"

    print("✅ /create_account page access check passed\n")


def test_forgot_password_page_access(test_environment):
    """
    Tests that the public /forgot_password page is accessible and returns HTML.
    Expected: ✅ PASS (200 OK)
    """
    
    print("\n\n🌐 Starting Test: /forgot_password page access")
    url = f"{TEST_SERVER}/forgot_password"
    print(f"➡️  Requesting: {url} (Expected 200 OK)")
    
    # --- Request ---
    resp = requests.get(url, timeout=5)
    
    print(f"⬇️  Response code: {resp.status_code}")
    
    # --- Assertions ---
    assert resp.status_code == 200, f"❌ Expected 200 from {url}, got {resp.status_code}"
    
    # Check that it returned HTML
    assert "text/html" in resp.headers.get("Content-Type", ""), f"❌ Expected Content-Type 'text/html', got {resp.headers.get('Content-Type')}"

    print("✅ /forgot_password page access check passed\n")

