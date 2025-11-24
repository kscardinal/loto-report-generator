import subprocess
import time
import requests
import pytest
import os


COMPOSE_FILES = [
    "docker-compose.yml",
    "docker-compose.test.yml",
]

PROJECT_NAME = "app_pytest_env"  # fully isolated docker namespace


@pytest.fixture(scope="session")
def test_environment():
    # --- Start stack ---
    print("\n🚀 Starting test docker environment...\n")

    result = subprocess.run(
        ["docker", "compose", *sum([["-f", f] for f in COMPOSE_FILES], []),
         "-p", PROJECT_NAME, "up", "--build", "-d"],
        env=os.environ,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    result.check_returncode()

    # --- Wait for FastAPI ---
    url = "http://localhost:8100/health"

    for i in range(30):
        try:
            r = requests.get(url)
            if r.status_code == 200:
                print("✅ Test server is up!")
                break
        except Exception:
            pass
        print(f"⏳ Waiting for backend... ({i}/30)")
        time.sleep(1)
    else:
        raise RuntimeError("Backend did not start in time.")

    yield  # tests run here

    # --- Tear down ---
    print("\n🧹 Tearing down docker test environment...\n")
    subprocess.run(
        ["docker", "compose", *sum([["-f", f] for f in COMPOSE_FILES], []),
         "-p", PROJECT_NAME, "down", "-v"],
        check=False
    )
