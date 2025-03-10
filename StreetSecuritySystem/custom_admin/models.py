import requests

# Firebase Realtime Database Configuration
API_KEY = "AIzaSyBTZtfc-W-MEAm5eLpoAXMw1vfbwg_5R1g"
DATABASE_URL = "https://streetsecuritysystem-default-rtdb.firebaseio.com/"

def fetch_logs():
    """
    Fetch logs from Firebase Realtime Database.
    """
    logs = []
    try:
        response = requests.get(f"{DATABASE_URL}/events.json")
        if response.status_code == 200 and response.json() is not None:
            logs_data = response.json()
            logs = [
                {
                    "timestamp": v.get("timestamp", "N/A"),
                    "event": v.get("event_type", "Unknown Event"),
                    "location": v.get("location", "Unknown Location"),
                    "details": v.get("details", "No details available")
                }
                for v in logs_data.values()
            ]
        else:
            print("⚠ No logs found in Firebase Database.")
    except Exception as e:
        print(f"❌ Error fetching logs: {str(e)}")

    return logs
