from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests


API_KEY = "AIzaSyBTZtfc-W-MEAm5eLpoAXMw1vfbwg_5R1g"
DATABASE_URL = "https://streetsecuritysystem-default-rtdb.firebaseio.com/"

def index(request):
    return render(request, "index.html")

def complaint(request):
    return render(request, "complaint.html")

@csrf_exempt  
def submit_complaint(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))  


            required_fields = ["firstName", "lastName", "phoneNo", "area", "complaintDetails", "categories"]
            for field in required_fields:
                if field not in data or not data[field]:
                    return JsonResponse({"error": f"Missing required field: {field}"}, status=400)


            complaint_data = {
                "firstName": data["firstName"],
                "lastName": data["lastName"],
                "phoneNo": data["phoneNo"],
                "area": data["area"],
                "complaintDetails": data["complaintDetails"],
                "categories": data["categories"],  # Include selected categories
                "timestamp": "Pending"  # Will be set by Firebase
            }


            response = requests.post(f"{DATABASE_URL}/complaints.json", json=complaint_data)
            
            if response.status_code == 200:
                return JsonResponse({"message": "Complaint submitted successfully!"}, status=200)
            else:
                return JsonResponse({"error": "Failed to store complaint in Firebase"}, status=500)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)
