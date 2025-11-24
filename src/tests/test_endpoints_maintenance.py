# ==============================================================================
# 🗃️ Import Setup
# ==============================================================================
import os
import pytest
import requests
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import shutil
import subprocess
import time

# Database Imports
import pymongo
import gridfs
from contextlib import ExitStack

# Assuming your FastAPI application defines the necessary functions
from ..api.auth_utils import create_access_token 


# ==============================================================================
# ⚙️ Configuration and Docker Setup Variables
# ==============================================================================
TEST_SERVER = "http://localhost:8100"
COMPOSE_FILES = ["docker-compose.yml", "docker-compose.test.yml"]
PROJECT_NAME = "app_pytest_env"
REQUEST_TIMEOUT = 5 
CONTAINER_TEMP_DIR = "/app/temp" 
DB_NAME = "test_db" # Must match the database name used by your FastAPI app

# FIX: Corrected path for mocking the email function
EMAIL_FUNCTION_PATH = "src.api.main.send_email_auto" 
GRIDFS_PATH = "src.api.main.fs" 
UPLOADS_COLLECTION_PATH = "src.api.main.uploads"

# Skip tests if no server or requests not available
if not TEST_SERVER or not requests:
    reason = (f"Skipping tests: TEST_HOST (or SERVER_IP) not configured or 'requests' not available ")
    pytest.skip(reason, allow_module_level=True)


# -----------------------------
# JWT setup (Owner, Admin, Unauthorized)
# -----------------------------
OWNER_USERNAME = "owner_test"
OWNER_TOKEN = create_access_token({"sub": OWNER_USERNAME, "role": "owner"})
OWNER_HEADERS = {"Authorization": f"Bearer {OWNER_TOKEN}"}

ADMIN_USERNAME = "admin_test"
ADMIN_TOKEN = create_access_token({"sub": ADMIN_USERNAME, "role": "admin"})
ADMIN_HEADERS = {"Authorization": f"Bearer {ADMIN_TOKEN}"}

USER_USERNAME = "user_test"
USER_TOKEN = create_access_token({"sub": USER_USERNAME, "role": "user"})
USER_HEADERS = {"Authorization": f"Bearer {USER_TOKEN}"}

# === Resolve project paths for local cleanup ===
PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_DIR = PROJECT_ROOT / "src" / "tests"
TEMP_DIR = PROJECT_ROOT / "temp" # Local path to the shared temp directory
TEMP_DIR.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# 🛠️ Docker & Utility Functions
# ==============================================================================

def build_compose_command(command, services=None):
    """Builds the base 'docker compose' command with files and project name."""
    file_args = sum([["-f", f] for f in COMPOSE_FILES], [])
    cmd = ["docker", "compose", *file_args, "-p", PROJECT_NAME, command]
    if services:
        cmd.extend(services)
    return cmd

def docker_exec_cmd(command):
    """Executes a command inside the backend container."""
    exec_command = build_compose_command("exec", ["backend", "sh", "-c", command])
    
    result = subprocess.run(
        exec_command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
        timeout=10
    )
    return result.stdout.strip()

def setup_docker_test_files(count=5):
    """Creates test files and a subdirectory inside the backend container's temp folder."""
    docker_exec_cmd(f"mkdir -p {CONTAINER_TEMP_DIR}")
    docker_exec_cmd(f"mkdir -p {CONTAINER_TEMP_DIR}/test_subdir")
    
    for i in range(count):
        docker_exec_cmd(f"echo 'test content' > {CONTAINER_TEMP_DIR}/test_file_{i}.txt")
    
def count_docker_files():
    """Counts only the files inside the container's temp folder."""
    try:
        count_output = docker_exec_cmd(f"find {CONTAINER_TEMP_DIR} -maxdepth 1 -type f | wc -l")
        return int(count_output)
    except subprocess.CalledProcessError as e:
        print(f"Error counting files in container: {e.stderr}")
        return -1

def count_docker_items():
    """Counts all items (files/dirs) inside the container's temp folder."""
    try:
        count_output = docker_exec_cmd(f"ls -A {CONTAINER_TEMP_DIR} | wc -l")
        return int(count_output)
    except subprocess.CalledProcessError as e:
        print(f"Error counting items in container: {e.stderr}")
        return -1
    
def get_backend_logs():
    """Fetches and prints the logs for the backend service."""
    print("\nAttempting to fetch backend logs...")
    try:
        log_command = build_compose_command("logs", ["backend"])
        
        log_result = subprocess.run(
            log_command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
            timeout=10
        )
        print("\n================== BACKEND CONTAINER LOGS ==================\n")
        print(log_result.stdout)
        print("\n============================================================\n")
    except subprocess.CalledProcessError as e:
        print(f"Failed to fetch backend logs. Error details:\n{e.stderr}", file=sys.stderr)
    except FileNotFoundError:
        print("Error: 'docker compose' command not found. Is Docker installed and in PATH?", file=sys.stderr)
    except subprocess.TimeoutExpired:
        print("Timeout while trying to fetch backend logs.", file=sys.stderr)


# ==============================================================================
# 💾 MongoDB / GridFS Utility Functions
# ==============================================================================

def get_test_db(db_name=DB_NAME):
    """Connects to the MongoDB service and returns the specified database object."""
    MONGO_URL = "mongodb://localhost:27117" 
    MONGO_USER = "testuser"
    MONGO_PASSWORD = "testpass"

    client = pymongo.MongoClient(
        MONGO_URL,
        username=MONGO_USER,
        password=MONGO_PASSWORD
    )
    return client[db_name]


def insert_orphan_photos(db, count=2):
    """Inserts files directly into GridFS that have no associated records, making them 'orphans'."""
    fs = gridfs.GridFS(db)
    inserted_ids = []
    
    for i in range(count):
        # Create a dummy photo file
        file_id = fs.put(
            b"dummy_photo_data_for_test", # This is the dummy content
            filename=f"orphan_test_photo_{i}.jpg",
            content_type="image/jpeg"
        )
        inserted_ids.append(file_id)
        
    print(f"   -> Inserted {count} orphan photos into GridFS.")
    return inserted_ids

def count_photos_in_gridfs(db):
    """Returns the total number of entries in the fs.files collection."""
    return db["fs.files"].count_documents({})


# ==============================================================================
# 🐳 Pytest Fixtures (Test Environment Setup/Teardown)
# ==============================================================================

@pytest.fixture(scope="session")
def test_environment():
    """
    Sets up a session-scoped Docker Compose test environment.
    Starts the containers, waits for the backend, yields, and tears down.
    """
    from contextlib import ExitStack
    with ExitStack() as stack:
        # --- Start stack ---
        print("\n🚀 Starting test docker environment...\n")
        
        up_command = build_compose_command("up", ["--build", "-d"])

        result = subprocess.run(
            up_command,
            env=os.environ,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )

        if result.returncode != 0:
            print("\n❌ Docker Compose 'up' failed! See STDERR above.", file=sys.stderr)
            get_backend_logs() 
            result.check_returncode() 
        
        def teardown_docker():
            print("\n\n🧹 Tearing down docker test environment...\n")
            down_command = build_compose_command("down", ["-v"]) 
            subprocess.run(
                down_command,
                capture_output=True,
                check=False
            )
            
        stack.callback(teardown_docker)

        # --- Wait for Backend Service ---
        url = "http://localhost:8100/health"
        timeout_seconds = 240
        
        print(f"\n⏳ Waiting for backend at {url} (Timeout: {timeout_seconds}s)...")

        for i in range(timeout_seconds):
            try:
                r = requests.get(url, timeout=REQUEST_TIMEOUT) 
                if r.status_code == 200:
                    print("\n✅ Test server is up and healthy!")
                    break
            except requests.exceptions.ConnectionError:
                pass
            except requests.exceptions.RequestException as e:
                print(f"Service returned error: {e}") 
                pass
                
            print(f"⏳ Retrying... ({i+1}/{timeout_seconds})")
            time.sleep(1)
        else:
            get_backend_logs()
            raise RuntimeError(
                f"Backend service at {url} did not become healthy within {timeout_seconds} seconds. Check logs above."
            )

        # 3. Yield to run tests
        yield 

@pytest.fixture(autouse=True)
def cleanup_docker_temp_dir():
    """Cleans up the container's temp directory before and after tests."""
    # Teardown logic
    yield
    
    print("\n🧹 Ensuring Docker temp directory is clean...")
    try:
        # Recursively remove all contents of the container's temp directory
        docker_exec_cmd(f"rm -rf {CONTAINER_TEMP_DIR}/*")
        # Recreate the base directory structure if it was deleted
        docker_exec_cmd(f"mkdir -p {CONTAINER_TEMP_DIR}")
    except Exception as e:
        # This can happen if the container is already down or still starting
        print(f"Warning: Could not clean up Docker temp dir. {e}")


# ==============================================================================
# 🧪 TESTS
# ==============================================================================

# -----------------------------
# Cleanup Endpoint Tests (/cleanup_orphan_photos)
# -----------------------------

@patch(EMAIL_FUNCTION_PATH, MagicMock()) 
def test_cleanup_orphan_photos_success_with_owner(test_environment):
    """Tests /cleanup_orphan_photos access with an 'owner' role token."""
    
    print("\n\n🌐 Starting Test: /cleanup_orphan_photos with OWNER role")
    url = f"{TEST_SERVER}/cleanup_orphan_photos"
    resp = requests.get(url, headers=OWNER_HEADERS, timeout=30) 
    
    print(f"⬇️ Response code: {resp.status_code}")
    
    assert resp.status_code == 200, f"❌ Expected 200 from {url}, got {resp.status_code}"
    print("✅ Orphan photo cleanup passed for OWNER role\n")


@patch(EMAIL_FUNCTION_PATH, MagicMock()) 
def test_cleanup_orphan_photos_success_with_admin(test_environment):
    """Tests /cleanup_orphan_photos access with the minimum required 'admin' role."""
    
    print("\n\n🌐 Starting Test: /cleanup_orphan_photos with ADMIN role")
    url = f"{TEST_SERVER}/cleanup_orphan_photos"
    resp = requests.get(url, headers=ADMIN_HEADERS, timeout=30) 
    
    print(f"⬇️ Response code: {resp.status_code}")
    
    assert resp.status_code == 200, f"❌ Expected 200 from {url}, got {resp.status_code}"
    print("✅ Orphan photo cleanup passed for ADMIN role\n")


@patch(EMAIL_FUNCTION_PATH, MagicMock()) 
def test_cleanup_orphan_photos_performs_deletion(test_environment):
    """
    Tests /cleanup_orphan_photos end-to-end by inserting orphan files 
    into GridFS and verifying their deletion.
    """
    db = get_test_db(db_name=DB_NAME)

    # 1. Setup: Insert orphan files
    initial_photo_count = count_photos_in_gridfs(db)
    inserted_ids = insert_orphan_photos(db, count=3) # Store the IDs if needed
    current_photo_count = count_photos_in_gridfs(db)
    
    print(f" -> Count after inserting orphans: {current_photo_count}")
    
    assert current_photo_count == initial_photo_count + 3, "❌ Setup failed: Did not insert 3 photos."

    url = f"{TEST_SERVER}/cleanup_orphan_photos"
    
    # --- Request (as Admin) ---
    # The request is sent to the running server.
    resp = requests.get(url, headers=ADMIN_HEADERS, timeout=30) 
    assert resp.status_code == 200, f"❌ Expected 200, got {resp.status_code}"
    
    # 2. Verification: Check MongoDB state
    final_photo_count = count_photos_in_gridfs(db)
    print(f" -> Final count after cleanup: {final_photo_count}")
    
    # Assert that the cleanup removed the inserted orphans.
    assert final_photo_count == initial_photo_count, \
        f"❌ Deletion failed: Expected final count of {initial_photo_count}, got {final_photo_count}."
        
    data = resp.json()
    assert len(data.get("deleted")) == 3, f"❌ Expected 3 files deleted, got {len(data.get('deleted'))}."

    print("✅ Orphan photo cleanup and deletion verified\n")


def test_cleanup_orphan_photos_insufficient_permissions(test_environment):
    """Tests that a standard 'user' role is denied access (403 Forbidden)."""
    
    print("\n\n🌐 Starting Test: /cleanup_orphan_photos with UNAUTHORIZED USER role")
    url = f"{TEST_SERVER}/cleanup_orphan_photos"
    resp = requests.get(url, headers=USER_HEADERS, timeout=10)
    
    print(f"⬇️ Response code: {resp.status_code}")
    
    assert resp.status_code == 403, f"❌ Expected 403 from {url}, got {resp.status_code}"
    
    data = resp.json()
    assert data.get("detail") == "Insufficient permissions", f"❌ Unexpected error message: {data}"

    print("✅ Orphan photo cleanup insufficient permissions check passed (403)\n")


def test_cleanup_orphan_photos_unauthenticated(test_environment):
    """Tests that an unauthenticated request is denied access (401 Unauthorized)."""
    
    print("\n\n🌐 Starting Test: /cleanup_orphan_photos with NO TOKEN (Unauthenticated)")
    url = f"{TEST_SERVER}/cleanup_orphan_photos"
    resp = requests.get(url, timeout=10)
    
    print(f"⬇️ Response code: {resp.status_code}")
    
    assert resp.status_code == 401, f"❌ Expected 401 from {url}, got {resp.status_code}"
    
    data = resp.json()
    assert "Not authenticated" in data.get("detail"), f"❌ Unexpected error message: {data}"

    print("✅ Orphan photo cleanup unauthenticated check passed (401)\n")


# -----------------------------
# Clear Temp Endpoint Tests (/clear/)
# -----------------------------

def test_clear_temp_folders_end_to_end_deletion_docker(test_environment):
    """
    Tests /clear/ by creating files INSIDE the Docker container and 
    verifying they are deleted after the API call.
    """
    
    # 1. Setup: Create test files INSIDE the Docker container
    setup_docker_test_files(count=5)
    
    initial_file_count = count_docker_files()
    initial_item_count = count_docker_items()
    
    print(f"\n\n📁 Initial files INSIDE CONTAINER: {initial_file_count} (Total items: {initial_item_count})")
    assert initial_file_count == 5, f"❌ Setup failed: Expected 5 files inside container, found {initial_file_count}."
    assert initial_item_count == 6, f"❌ Setup failed: Expected 6 items (5 files + 1 dir)."
    
    print("🌐 Starting Test: /clear/ Real Deletion (Docker Exec)")
    url = f"{TEST_SERVER}/clear/"
    
    # --- Request ---
    resp = requests.post(url, headers=USER_HEADERS, timeout=10)
    
    print(f"⬇️ Response code: {resp.status_code}")
    
    # --- Assertions ---
    assert resp.status_code == 200, f"❌ Expected 200, got {resp.status_code}"
    
    # 2. Verification: Check final state INSIDE the Docker container
    final_file_count = count_docker_files()
    final_item_count = count_docker_items()
    
    print(f"📁 Final files INSIDE CONTAINER: {final_file_count} (Total items: {final_item_count})")
    
    assert final_file_count == 0, \
        f"❌ Deletion failed: {final_file_count} files remaining inside container, expected 0."
    assert final_item_count == 1, \
        f"❌ Directory deletion failed: {final_item_count} items remaining, expected 1 directory."

    print("✅ /clear/ End-to-End Deletion verified\n")


def test_clear_temp_folders_unauthenticated(test_environment):
    """Tests that an unauthenticated request to /clear/ is denied access (401 Unauthorized)."""
    
    print("\n\n🌐 Starting Test: /clear/ with NO TOKEN (Unauthenticated)")
    url = f"{TEST_SERVER}/clear/"
    resp = requests.post(url, timeout=10)
    
    print(f"⬇️ Response code: {resp.status_code}")
    
    assert resp.status_code == 401, f"❌ Expected 401 from {url}, got {resp.status_code}"
    
    data = resp.json()
    assert "Not authenticated" in data.get("detail"), f"❌ Unexpected error message: {data}"

    print("✅ /clear/ unauthenticated check passed (401)\n")