from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

from .models import Task
from .serializers import TaskSerializer


# Create your views here.
class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [ IsAuthenticated ]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        self.broadcast_task_change('create', instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self.broadcast_task_change('update', instance)

    def perform_destroy(self, instance):
        task_id = instance.id
        task_data = TaskSerializer(instance).data
        super().perform_destroy(instance)
        task_data[ 'id' ] = task_id  # Ensure we have the ID for the frontend
        self.broadcast_task_change('delete', task_data, is_instance=False)

    def broadcast_task_change(self, action, instance, is_instance=True):
        channel_layer = get_channel_layer()
        data = {
            'type': 'task_event',
            'action': action,
            'task': TaskSerializer(instance).data if is_instance else instance
        }
        async_to_sync(channel_layer.group_send)('tasks_group', data)


class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)


class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    template_name = 'tasks/task_form.html'
    fields = [ 'title', 'description', 'status' ]
    success_url = reverse_lazy('task-list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)

        # Broadcast the task creation via WebSocket
        channel_layer = get_channel_layer()
        data = {
            'type': 'task_event',
            'action': 'create',
            'task': TaskSerializer(self.object).data
        }
        async_to_sync(channel_layer.group_send)('tasks_group', data)

        return response


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    template_name = 'tasks/task_form.html'
    fields = [ 'title', 'description', 'status' ]
    success_url = reverse_lazy('task-list')

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)

        # Broadcast the task update via WebSocket
        channel_layer = get_channel_layer()
        data = {
            'type': 'task_event',
            'action': 'update',
            'task': TaskSerializer(self.object).data
        }
        async_to_sync(channel_layer.group_send)('tasks_group', data)

        return response


class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    success_url = reverse_lazy('task-list')

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        task_data = TaskSerializer(self.object).data
        success_url = self.get_success_url()

        # Get task ID before deletion
        task_id = self.object.id

        # Delete the object
        self.object.delete()

        # Broadcast the task deletion via WebSocket
        channel_layer = get_channel_layer()
        data = {
            'type': 'task_event',
            'action': 'delete',
            'task': task_data
        }
        async_to_sync(channel_layer.group_send)('tasks_group', data)

        return redirect(success_url)


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('task-list')
    else:
        form = UserCreationForm()
    return render(request, 'tasks/register.html', {'form': form})
