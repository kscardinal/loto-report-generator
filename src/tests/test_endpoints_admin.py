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

def test_health_check_success(test_environment):
    """Tests that the public /health endpoint returns a 200 OK status."""
    
    print("\n\n🌐  Starting Test: /health public access")
    url = f"{TEST_SERVER}/health"
    print(f"➡️  Requesting: {url}")
    
    # --- Request ---
    resp = requests.get(url, timeout=5)
    
    print(f"⬇️  Response code: {resp.status_code}")
    
    # --- Assertions ---
    assert resp.status_code == 200, f"❌ Expected 200 from {url}, got {resp.status_code}"
    
    data = resp.json()
    print(f"📬 Response JSON: {data}")
    assert data == {"status": "ok"}, f"❌ Health status unexpected: {data}"

    print("✅ /health check passed\n")


def test_db_status_success_with_owner(test_environment):
    """Tests /db_status access with an 'owner' role token (since owner > admin)."""
    
    print("\n\n🌐 Starting Test: /db_status with OWNER role")
    url = f"{TEST_SERVER}/db_status"
    print(f"➡️  Requesting: {url}")
    
    # --- Request ---
    resp = requests.get(url, headers=OWNER_HEADERS, timeout=10) 
    
    print(f"⬇️  Response code: {resp.status_code}")
    
    # --- Assertions ---
    assert resp.status_code == 200, f"❌ Expected 200 from {url}, got {resp.status_code}"
    
    data = resp.json()
    print(f"📬 Response JSON: {data}")
    assert data.get("status") == "ok", f"❌ DB status unexpected: {data}"
    assert "successful" in data.get("message"), f"❌ Message missing 'successful': {data}"
    
    print("✅ DB status passed for OWNER role\n")


def test_db_status_success_with_admin(test_environment):
    """Tests /db_status access with the minimum required 'admin' role."""
    
    print("\n\n🌐 Starting Test: /db_status with ADMIN role")
    url = f"{TEST_SERVER}/db_status"
    print(f"➡️  Requesting: {url}")
    
    # --- Request ---
    resp = requests.get(url, headers=ADMIN_HEADERS, timeout=10) 
    
    print(f"⬇️  Response code: {resp.status_code}")
    
    # --- Assertions ---
    assert resp.status_code == 200, f"❌ Expected 200 from {url}, got {resp.status_code}"
    
    data = resp.json()
    print(f"📬 Response JSON: {data}")
    assert data.get("status") == "ok", f"❌ DB status unexpected: {data}"
    assert "successful" in data.get("message"), f"❌ Message missing 'successful': {data}"

    print("✅ DB status passed for ADMIN role\n")


def test_db_status_insufficient_permissions(test_environment):
    """Tests that a standard 'user' role is denied access (403 Forbidden)."""
    
    print("\n\n🌐 Starting Test: /db_status with UNAUTHORIZED USER role")
    url = f"{TEST_SERVER}/db_status"
    print(f"➡️  Requesting: {url}")
    
    # --- Request ---
    resp = requests.get(url, headers=USER_HEADERS, timeout=10)
    
    print(f"⬇️  Response code: {resp.status_code}")
    
    # --- Assertions ---
    assert resp.status_code == 403, f"❌ Expected 403 from {url}, got {resp.status_code}"
    
    data = resp.json()
    print(f"📬 Response JSON: {data}")
    assert data.get("detail") == "Insufficient permissions", f"❌ Unexpected error message: {data}"

    print("✅ Insufficient permissions check passed (403)\n")


def test_db_status_unauthenticated(test_environment):
    """Tests that an unauthenticated request is denied access (401 Unauthorized)."""
    
    print("\n\n🌐 Starting Test: /db_status with NO TOKEN (Unauthenticated)")
    url = f"{TEST_SERVER}/db_status"
    print(f"➡️  Requesting: {url}")
    
    # --- Request ---
    resp = requests.get(url, timeout=10)
    
    print(f"⬇️  Response code: {resp.status_code}")
    
    # --- Assertions ---
    assert resp.status_code == 401, f"❌ Expected 401 from {url}, got {resp.status_code}"
    
    data = resp.json()
    print(f"📬 Response JSON: {data}")
    assert "Not authenticated" in data.get("detail"), f"❌ Unexpected error message: {data}"

    print("✅ Unauthenticated check passed (401)\n")

