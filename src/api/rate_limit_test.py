import requests
import time
import threading

TARGET_URL = "https://lotogenerator.app/"
NUM_REQUESTS = 20
REQUESTS_PER_SECOND = 20  # This is the rate we are testing (20r/s > 5r/s limit)

def make_request(url, request_id):
    try:
        # Use HEAD or GET, HEAD is often faster as it doesn't download the body
        response = requests.head(url, verify=False, timeout=5) 
        print(f"Request #{request_id}: Status Code {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Request #{request_id}: Error - {e}")

threads = []
print(f"Starting to send {NUM_REQUESTS} requests at {REQUESTS_PER_SECOND}r/s to {TARGET_URL}...")
print("------------------------------------------------------------------------")

# Calculate the sleep time needed to achieve the desired RPS
sleep_duration = 1.0 / REQUESTS_PER_SECOND

for i in range(1, NUM_REQUESTS + 1):
    thread = threading.Thread(target=make_request, args=(TARGET_URL, i))
    threads.append(thread)
    thread.start()
    time.sleep(sleep_duration)

# Wait for all threads to complete
for thread in threads:
    thread.join()
    
print("------------------------------------------------------------------------")
print("Test complete.")