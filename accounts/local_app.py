"""Shutdown is available only in a launcher-owned, loopback-only process."""
import threading
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

_stop = None

def register_shutdown(callback):
    global _stop
    _stop = callback

def available():
    return _stop is not None

@login_required
@require_http_methods(['GET', 'POST'])
def shutdown(request):
    if not available() or request.META.get('REMOTE_ADDR') not in ('127.0.0.1', '::1'):
        raise PermissionDenied('Afsluiten kan alleen in de lokaal gestarte toepassing.')
    stopped = request.method == 'POST'
    if stopped:
        # Allow the HTTP response to finish before closing the owned server.
        timer = threading.Timer(.8, _stop)
        timer.daemon = True
        timer.start()
    return render(request, 'accounts/shutdown.html', {'stopped': stopped})
