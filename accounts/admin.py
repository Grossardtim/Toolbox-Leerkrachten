from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class TeacherAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'is_active', 'can_evaluate', 'can_export', 'is_superuser')
    list_filter = ('is_active', 'can_evaluate', 'can_export', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (('Programmaonderdelen', {'fields': ('can_evaluate', 'can_export')}),)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Profiel en toegang', {'fields': ('first_name', 'last_name', 'email', 'can_evaluate', 'can_export')}),)

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.site_header = 'Atheneum Tungrorum · Accountbeheer'
admin.site.site_title = 'Accountbeheer'
admin.site.index_title = 'Leerkrachten en toegang'
