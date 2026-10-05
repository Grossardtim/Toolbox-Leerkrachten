"""Serialize local requests so a confirmed restore cannot interleave app writes."""
from threading import RLock
from django.conf import settings
lock = RLock()

class LocalMaintenanceMiddleware:
    def __init__(self, get_response): self.get_response = get_response
    def __call__(self, request):
        if settings.DEBUG or settings.STANDALONE:
            with lock: return self.get_response(request)
        return self.get_response(request)

