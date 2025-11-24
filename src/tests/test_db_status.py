import os
import pytest
from ..api.auth_utils import create_access_token

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

# Determine which server to use based on environment
APP_ENV = os.getenv("APP_ENV", "dev").lower()

if APP_ENV == "dev":
    TEST_SERVER = os.getenv("TEST_SERVER_IP")
else:
    TEST_SERVER = os.getenv("SERVER_IP")

# Skip tests if no server or requests not available
if not TEST_SERVER or not requests:
    reason = (
        f"Skipping db_status tests: SERVER_IP not configured or 'requests' not available "
        f"(APP_ENV={APP_ENV})"
    )
    pytest.skip(reason, allow_module_level=True)

# -----------------------------
# JWT setup
# -----------------------------
TEST_USERNAME = "testuser"
TEST_TOKEN = create_access_token({"sub": TEST_USERNAME, "role": "admin"})

# Headers for mobile/API endpoints
HEADERS = {"Authorization": f"Bearer {TEST_TOKEN}"}

# Cookies for web endpoints
COOKIES = {"access_token": TEST_TOKEN}


def test_db_status_endpoint_responds_ok():
    """Call /db_status on the configured SERVER_IP with JWT and assert DB reports 'ok'."""

    url = TEST_SERVER.rstrip("/") + "/db_status"
    print("\n\n🔎 DB status check\n")
    print(f"➡️  Requesting: {url}")

    # Try mobile/API approach first
    resp = requests.get(url, headers=HEADERS, timeout=10)

    # If unauthorized, try web/cookie approach
    if resp.status_code in (401, 403):
        print("⚠️  Mobile/API JWT unauthorized, trying web cookie method")
        resp = requests.get(url, cookies=COOKIES, timeout=10)

    print(f"⬇️  Response code: {resp.status_code}")

    try:
        data = resp.json()
        print(f"📬 Response JSON: {data}")
    except ValueError:
        print(f"❌ Response from {url} was not JSON: {resp.text}")
        pytest.fail(f"Response from {url} was not JSON: {resp.text}")

    assert resp.status_code == 200, f"Expected 200 from {url}, got {resp.status_code}"
    assert data.get("status") == "ok", f"DB status unexpected: {data}"

    print("✅ Database connection reported 'ok'\n")
