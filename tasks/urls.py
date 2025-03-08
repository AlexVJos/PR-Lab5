from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'tasks', views.TaskViewSet, basename='task')

urlpatterns = [
    # API routes
    path('api/', include(router.urls)),

    # # Web routes
    # path('', views.TaskListView.as_view(), name='task-list'),
    # path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task-detail'),
    # path('tasks/create/', views.TaskCreateView.as_view(), name='task-create'),
    # path('tasks/<int:pk>/update/', views.TaskUpdateView.as_view(), name='task-update'),
    # path('tasks/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task-delete'),
    # path('register/', views.register, name='register'),
]