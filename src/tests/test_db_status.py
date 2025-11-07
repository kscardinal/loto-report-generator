import os
import pytest

try:
    import requests
except Exception:  # pragma: no cover - defensive import for environments without requests
    requests = None

# Skip the entire module if TEST_SERVER_IP is not configured (same pattern as other tests)
TEST_SERVER = os.getenv("SERVER_IP")
if not TEST_SERVER or not requests:
    reason = (
        "Skipping db_status tests: SERVER_IP is not configured or 'requests' not available"
    )
    pytest.skip(reason, allow_module_level=True)


def test_db_status_endpoint_responds_ok():
    """Call /db_status on the configured SERVER_IP and assert the DB reports 'ok'.

    This test prints short, emoji-prefixed status lines so it's easy to follow in
    the pytest output (mirrors the style used in `test_pdf_scripts.py`).
    """
    url = TEST_SERVER.rstrip("/") + "/db_status"
    print("\n\n🔎 DB status check\n")
    print(f"➡️  Requesting: {url}")

    resp = requests.get(url, timeout=10)
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

