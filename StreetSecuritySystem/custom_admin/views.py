from django.shortcuts import render, redirect
from django.contrib import messages
import requests

API_KEY = "AIzaSyBTZtfc-W-MEAm5eLpoAXMw1vfbwg_5R1g"
DATABASE_URL = "https://streetsecuritysystem-default-rtdb.firebaseio.com/"

def admin_login(request):
    """
    Simple authentication for admin without Firebase.
    """
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        if email == "gouribiju913@gmail.com" and password == "admin42125":
            return redirect("admin_dashboard")  

        messages.error(request, "Invalid credentials")

    return render(request, "adminpanel/admin_login.html")

def view_logs(request):
    """
    Fetch logs from Firebase Realtime Database under `/events`.
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
            messages.error(request, "No logs found in Firebase Database.")
    except Exception as e:
        messages.error(request, f"Error fetching logs: {str(e)}")

    return render(request, "adminpanel/logs.html", {"logs": logs})



def admin_dashboard(request):
    """
    Admin dashboard page.
    """
    return render(request, "adminpanel/adminpanel.html")  


def admin_logout(request):
    return redirect("admin_login") 
