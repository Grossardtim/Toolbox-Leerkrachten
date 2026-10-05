from django.urls import path
from . import views
from .deletion import delete_record
from .coverage import coverage
urlpatterns = [
    path('doelenoverzicht/', coverage, name='coverage'),
    path('', views.home, name='home'),
    path('evaluaties/', views.dashboard, name='dashboard'),
    path('wissen/<str:kind>/<int:pk>/', delete_record, name='delete_record'),
    path('beheer/doelen/import/', views.goal_import, name='goal_import'),
    path('beheer/<str:kind>/', views.manage, name='manage'),
    path('beheer/<str:kind>/<int:pk>/', views.manage, name='manage_edit'),
    path('lessen/nieuw/', views.lesson_create, name='lesson_create'),
    path('lessen/<int:pk>/', views.lesson_detail, name='lesson'),
    path('lessen/<int:pk>/doelen/', views.lesson_goal_action, name='lesson_goal_action'),
]
