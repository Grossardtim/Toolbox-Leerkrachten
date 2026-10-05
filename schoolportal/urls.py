from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from accounts.views import PortalLoginView, teachers
from accounts.setup import first_setup
from accounts.local_app import shutdown
from accounts.releases import release_history
from accounts.preferences import preferences
from accounts.backups import backups, audit

urlpatterns = [
    path('beheerder/versies/', release_history, name='releases'),
    path('afsluiten/', shutdown, name='shutdown'),
    path('beheerder/backups/', backups, name='backups'),
    path('beheerder/logboek/', audit, name='audit'),
    path('instellingen/', preferences, name='preferences'),
    path('eerste-start/', first_setup, name='first_setup'),
    path('admin/login/', PortalLoginView.as_view()),
    path('admin/', admin.site.urls),
    path('aanmelden/', PortalLoginView.as_view(), name='login'),
    path('afmelden/', auth_views.LogoutView.as_view(), name='logout'),
    path('leerkrachten/', teachers, name='teachers'),
    path('leerkrachten/<int:pk>/', teachers, name='teacher_edit'),
    path('wachtwoord/', auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change.html', success_url='/'), name='password_change'),
    path('', include('evaluations.urls')),
    path('export/', include('exports.urls')),
]
