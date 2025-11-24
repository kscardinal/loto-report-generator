import requests

def test_health_check(test_environment):
    """Verify that the FastAPI test instance responds."""
    r = requests.get("http://localhost:8100/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
