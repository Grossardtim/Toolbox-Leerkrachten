"""First account creation is limited to an empty, local desktop installation."""
import os
from django.conf import settings
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from .forms import FirstAdminForm
from .models import User


@never_cache
@require_http_methods(['GET','POST'])
def first_setup(request):
    if not settings.STANDALONE or request.META.get('REMOTE_ADDR') not in ('127.0.0.1','::1') or User.objects.exists():
        raise Http404
    form=FirstAdminForm(request.POST or None,initial={'username':'beheerder'})
    if request.method=='POST' and form.is_valid():
        path=settings.DATA_DIR/'.setup.lock'
        try:fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
        except FileExistsError:return HttpResponse('De eerste installatie is al bezig.',status=409)
        try:
            with transaction.atomic():
                if User.objects.exists():raise Http404
                user=form.save(commit=False)
                user.is_staff=True;user.is_superuser=True
                user.save()
            return redirect('login')
        finally:
            os.close(fd);path.unlink(missing_ok=True)
    return render(request,'registration/first_setup.html',{'form':form})
