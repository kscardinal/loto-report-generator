# cron_executor.py
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
API_URL = os.getenv("CLEANUP_URL")
CRON_SECRET_KEY = os.getenv("ADMIN_JWT") 

def execute_cleanup_endpoint():
    print(f"[{datetime.now()}] Attempting to trigger FastAPI cleanup endpoint...")
    print(f"[{datetime.now()}] Connecting to {API_URL}")
    
    if not CRON_SECRET_KEY:
        print("ERROR: ADMIN_JWT is not set. Cannot authenticate.")
        return

    # Use the correct Authorization: Bearer header format
    headers = {
        "Authorization": f"Bearer {CRON_SECRET_KEY}" 
    }
    
    try:
        response = requests.post(API_URL, headers=headers, timeout=300)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        data = response.json()
        
        # --- Print Detailed Results ---
        print(f"[{datetime.now()}] SUCCESS! Cleanup task complete.")
        
        deleted_photos = data.get("deleted", {})
        total_photos_deleted = len(deleted_photos)
        
        if total_photos_deleted == 0:
            print("Status: No orphaned photos found or removed.")
        else:
            print(f"Status: {data.get('message', 'Cleanup complete.')}")
            
            # Print total space saved (Requires FastAPI endpoint to return this)
            total_size_saved = data.get("total_size_saved", "N/A")
            print(f"Total Space Saved: **{total_size_saved}**")
            
            print("\n-------------- Details of Deleted Files --------------")
            
            # Note: The FastAPI endpoint's `deleted_photos` dictionary currently contains
            # only the photo_name and photo_id. If you want the size of each photo, 
            # you must modify the FastAPI endpoint to return the size alongside the name.
            
            # Assuming deleted_photos = {"photo_id": "photo_name"}
            for pid, name in deleted_photos.items():
                # We can only print the name and ID here without modifying the server's return structure
                print(f"* ID: {pid} | Name: {name}") 
                
            # If your server endpoint returns more details, like: 
            # deleted_photos = {"photo_id": {"name": "photo_name", "size": "1.2 MB"}}
            # you would adapt the loop above to access the 'size' key.
            print("------------------------------------------------------")


    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now()}] ERROR: Failed to reach or execute endpoint.")
        print(f"Details: {e}")
        # Ensure we check if response exists before accessing response.text
        if 'response' in locals() and response.text:
            print(f"Server Error Message: {response.text}")
            # If unauthorized, print the specific reason
            if response.status_code == 401:
                print("Authentication Failed: Check if ADMIN_JWT is valid and has admin role.")

if __name__ == "__main__":
    execute_cleanup_endpoint()