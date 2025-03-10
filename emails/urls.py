from django.urls import path
from . import views

urlpatterns = [
    path('tasks/<int:task_id>/email/', views.send_task_email, name='send-task-email'),
    path('check-emails/', views.check_emails, name='check-emails'),
    path('test-email-protocols/', views.test_email_protocols, name='test-email-protocols'),
    path('dashboard/', views.dashboard, name='dashboard'),
]