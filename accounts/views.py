import hashlib
from datetime import timedelta
from django.contrib.auth.views import LoginView
from django.http import HttpResponse
from django.utils import timezone
from django.db import transaction
from .models import LoginThrottle
from .forms import UserChoiceAuthenticationForm, TeacherForm
from .models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.urls import reverse

class PortalLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    authentication_form = UserChoiceAuthenticationForm

    def dispatch(self, request, *args, **kwargs):
        from django.conf import settings
        if settings.STANDALONE and not User.objects.exists():
            return redirect('first_setup')
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Per account name, independent of spoofable forwarding headers.
        self.throttle_key = hashlib.sha256(request.POST.get('username', '').strip().casefold().encode()).hexdigest()
        now = timezone.now()
        item = LoginThrottle.objects.filter(key=self.throttle_key).first()
        if item and item.failures >= 5 and now - item.window_started < timedelta(minutes=15):
            return HttpResponse('Te veel aanmeldpogingen. Probeer over 15 minuten opnieuw.', status=429)
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        now = timezone.now()
        with transaction.atomic():
            item, _ = LoginThrottle.objects.select_for_update().get_or_create(
                key=self.throttle_key, defaults={'window_started': now})
            if now - item.window_started >= timedelta(minutes=15):
                item.failures = 0
                item.window_started = now
            item.failures += 1
            item.save()
        return super().form_invalid(form)

    def form_valid(self, form):
        LoginThrottle.objects.filter(key=self.throttle_key).delete()
        return super().form_valid(form)

@never_cache
@login_required
def teachers(request, pk=None):
    if not request.user.is_superuser:
        raise PermissionDenied('Alleen de overkoepelende beheerder kan leerkrachten beheren.')
    queryset = User.objects.filter(is_superuser=False).order_by('last_name', 'first_name', 'username')
    person = get_object_or_404(queryset, pk=pk) if pk else User(is_active=True)
    show_form = pk is not None or 'nieuw' in request.GET or request.method == 'POST'
    form = TeacherForm(request.POST if request.method == 'POST' else None, instance=person)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            person = form.save()
            from evaluations.views import log
            log(request.user, 'leerkracht gewijzigd' if pk else 'leerkracht aangemaakt', person)
        messages.success(request, f'Account {person.username} is opgeslagen.')
        return redirect('teachers')
    table = {'columns': ['Gebruikersnaam', 'Voornaam', 'Achternaam', 'E-mailadres', 'Actief', 'Evaluatietoegang', 'Exporttoegang'],
        'rows': [{'cells': [p.username, p.first_name, p.last_name, p.email,
                          'Ja' if p.is_active else 'Nee', 'Ja' if p.can_evaluate else 'Nee', 'Ja' if p.can_export else 'Nee'],
                  'url': reverse('teacher_edit', args=[p.pk]), 'action': 'Wijzigen',
                  'delete_url': reverse('delete_record', args=['leerkrachten', p.pk]), 'label': p.username} for p in queryset]}
    return render(request, 'accounts/teachers.html', {'people': queryset, 'table': table,
        'form': form, 'show_form': show_form, 'editing': pk is not None, 'nav':'teachers'})
