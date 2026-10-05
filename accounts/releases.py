from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from schoolportal.releases import RELEASES

@login_required
def release_history(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    return render(request, 'accounts/releases.html', {'releases':RELEASES,'nav':'releases'})
