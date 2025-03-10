from django.urls import path
from .views import (index, complaint, submit_complaint)

urlpatterns = [
    path("", index, name="index"),
    path("complaint/", complaint, name="complaint"),
    path("complaint/", submit_complaint, name="complaint"),
    path("submit_complaint/", submit_complaint, name="submit_complaint"),
]
