from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.shortcuts import render

from .models import Device


def home(request):
    """Display the devices of the park and their state."""
    devices = Device.objects.all()
    return render(request, "index.html", {"devices": devices})


def health(request):
    """Tell Docker whether the application and its database are working."""
    try:
        connection.ensure_connection()
    except DatabaseError:
        return JsonResponse({"status": "error", "database": "unreachable"}, status=503)
    return JsonResponse({"status": "ok"})
