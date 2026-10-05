def portal_context(request):
    from django.conf import settings
    from .models import Year
    from accounts.access import visible_records
    years = visible_records(Year, request.user) if request.user.is_authenticated else []
    from accounts.preferences import theme_css
    from accounts.local_app import available
    from schoolportal.releases import VERSION
    return {'portal_years': years, 'app_version': VERSION, 'local_shutdown': available(), 'development': settings.DEBUG, 'theme_css': theme_css(request.user)}
