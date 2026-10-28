from django.db import DatabaseError, connection
from django.http import JsonResponse


def health(request):
    """Tell Docker whether the application and its database are working."""
    try:
        connection.ensure_connection()
    except DatabaseError:
        return JsonResponse({"status": "error", "database": "unreachable"}, status=503)
    return JsonResponse({"status": "ok"})
