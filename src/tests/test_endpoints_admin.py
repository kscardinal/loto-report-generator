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
    reason = (
        f"Skipping tests: TEST_HOST (or SERVER_IP) not configured or 'requests' not available "
    )
    pytest.skip(reason, allow_module_level=True)

# -----------------------------
# JWT setup (Owner, Admin, Unauthorized)
# -----------------------------

# Owner User (Highest Role, should pass all admin checks)
OWNER_USERNAME = "owner_test"
OWNER_TOKEN = create_access_token({"sub": OWNER_USERNAME, "role": "owner"})
OWNER_HEADERS = {"Authorization": f"Bearer {OWNER_TOKEN}"}
OWNER_COOKIES = {"access_token": OWNER_TOKEN}

# Admin User (Authorized, should pass all admin checks)
ADMIN_USERNAME = "admin_test"
ADMIN_TOKEN = create_access_token({"sub": ADMIN_USERNAME, "role": "admin"})
ADMIN_HEADERS = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
ADMIN_COOKIES = {"access_token": ADMIN_TOKEN}

# Standard User (Unauthorized, should fail admin checks)
USER_USERNAME = "user_test"
USER_TOKEN = create_access_token({"sub": USER_USERNAME, "role": "user"})
USER_HEADERS = {"Authorization": f"Bearer {USER_TOKEN}"}
USER_COOKIES = {"access_token": USER_TOKEN}

# -----------------------------
# TESTS
# -----------------------------

# -----------------------------
# /health
# -----------------------------
def test_health_check_success(test_environment):
    """Tests that the public /health endpoint returns a 200 OK status."""
    url = f"{TEST_SERVER}/health"
    response = requests.get(url)
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# -----------------------------
# /db_status
# -----------------------------
def test_db_status_success_with_owner(test_environment):
    """Tests /db_status access with an 'owner' role token (since owner > admin)."""
    url = f"{TEST_SERVER}/db_status"
    
    response = requests.get(url, headers=OWNER_HEADERS) 
    
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "successful" in response.json()["message"]


def test_db_status_success_with_admin(test_environment):
    """Tests /db_status access with the minimum required 'admin' role."""
    url = f"{TEST_SERVER}/db_status"
    
    response = requests.get(url, headers=ADMIN_HEADERS) 
    
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "successful" in response.json()["message"]


def test_db_status_insufficient_permissions(test_environment):
    """Tests that a standard 'user' role is denied access (403 Forbidden)."""
    url = f"{TEST_SERVER}/db_status"
    
    response = requests.get(url, headers=USER_HEADERS)
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_db_status_unauthenticated(test_environment):
    """Tests that an unauthenticated request is denied access (401 Unauthorized)."""
    url = f"{TEST_SERVER}/db_status"
    
    response = requests.get(url)
    
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]