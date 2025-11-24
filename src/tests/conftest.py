import pytest
import subprocess
import os
import time
import requests
from contextlib import ExitStack
import sys # Added for more robust error printing

# Define the files and project name used for Docker Compose
# NOTE: Ensure these files exist in the directory where pytest is run.
COMPOSE_FILES = ["docker-compose.yml", "docker-compose.test.yml"]
PROJECT_NAME = "app_pytest_env"

# Increase the connection pool size to handle parallel requests if needed
# This modification applies globally to the requests library.
requests.adapters.DEFAULT_RETRIES = 5
# Also setting connect and read timeouts for requests is good practice
REQUEST_TIMEOUT = 5 

# --- Utility Function to Construct Docker Compose Command ---
def build_compose_command(command, services=None):
    """
    Builds the base 'docker compose' command with files and project name.
    e.g., ["docker", "compose", "-f", "f1.yml", "-f", "f2.yml", "-p", "proj", "up", ...]
    """
    # Flattens the list of ["-f", file] pairs
    file_args = sum([["-f", f] for f in COMPOSE_FILES], [])
    
    cmd = ["docker", "compose", *file_args, "-p", PROJECT_NAME, command]
    
    if services:
        cmd.extend(services)
        
    return cmd

# --- Utility Function to Get Logs on Failure ---
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
            check=True, # Raise exception if logs command fails
            timeout=10
        )
        print("\n================== BACKEND CONTAINER LOGS ==================\n")
        print(log_result.stdout)
        print("\n============================================================\n")
    except subprocess.CalledProcessError as e:
        # Note: 'e.stderr' contains the error output from the docker command
        print(f"Failed to fetch backend logs. Error details:\n{e.stderr}", file=sys.stderr)
    except FileNotFoundError:
        print("Error: 'docker compose' command not found. Is Docker installed and in PATH?", file=sys.stderr)
    except subprocess.TimeoutExpired:
        print("Timeout while trying to fetch backend logs.", file=sys.stderr)


@pytest.fixture(scope="session")
def test_environment():
    """
    Sets up a session-scoped Docker Compose test environment.
    Starts the containers, waits for the backend, yields, and tears down.
    """
    # Use ExitStack to ensure cleanup happens even if exceptions occur during setup
    with ExitStack() as stack:
        # --- Start stack ---
        print("\n🚀 Starting test docker environment...\n")
        
        up_command = build_compose_command("up", ["--build", "-d"])

        # 1. Start Docker stack
        result = subprocess.run(
            up_command,
            env=os.environ,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )

        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

        # Ensure docker compose command itself succeeded
        if result.returncode != 0:
             print("\n❌ Docker Compose 'up' failed! See STDERR above.", file=sys.stderr)
             get_backend_logs() # Try to get logs even if 'up' failed
             result.check_returncode() # Raise the CalledProcessError
        
        # 2. Register a cleanup action to stop the stack when the fixture scope ends
        def teardown_docker():
            print("\n🧹 Tearing down docker test environment...\n")
            down_command = build_compose_command("down", ["-v", "--rmi", "local"]) # Add --rmi local to remove images if needed
            subprocess.run(
                down_command,
                capture_output=True,
                check=False # Do not fail the tests if tear down fails
            )
            
        stack.callback(teardown_docker)

        # --- Wait for Backend Service (e.g., FastAPI) ---
        url = "http://localhost:8100/health"
        timeout_seconds = 240
        
        print(f"\n⏳ Waiting for backend at {url} (Timeout: {timeout_seconds}s)...")

        for i in range(timeout_seconds):
            try:
                # Use a request-level timeout
                r = requests.get(url, timeout=REQUEST_TIMEOUT) 
                if r.status_code == 200:
                    print("✅ Test server is up and healthy!")
                    break
            except requests.exceptions.ConnectionError:
                pass # Expected while the service is starting
            except requests.exceptions.RequestException as e:
                # Catch other request errors (e.g., 5xx status codes)
                print(f"Service returned error: {e}") 
                pass
                
            print(f"⏳ Retrying... ({i+1}/{timeout_seconds})")
            time.sleep(1)
        else:
            # If the loop completes without breaking (i.e., timeout)
            get_backend_logs() # <-- CRUCIAL: Print logs on timeout
            raise RuntimeError(
                f"Backend service at {url} did not become healthy within {timeout_seconds} seconds. Check logs above."
            )

        # 3. Yield to run tests
        yield 
        
    # Execution returns here after all tests have run
    # The teardown_docker function is automatically called by ExitStack