let taskSocket = null;

function connectWebSocket() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';

    taskSocket = new WebSocket(
        wsProtocol + window.location.host + '/ws/tasks/'
    );

    taskSocket.onopen = function(e) {
        console.log('WebSocket connection established');
    };

    taskSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        console.log('WebSocket message received:', data);

        if (data.type === 'task_event') {
            handleTaskEvent(data);
        }
    };

    taskSocket.onclose = function(e) {
        console.log('WebSocket connection closed');
        setTimeout(function() {
            console.log('Attempting to reconnect WebSocket...');
            connectWebSocket();
        }, 3000);
    };

    taskSocket.onerror = function(e) {
        console.error('WebSocket error:', e);
    };
}

function handleTaskEvent(data) {
    const action = data.action;
    const task = data.task;

    const currentPath = window.location.pathname;

    if (currentPath === '/' || currentPath.endsWith('/task-list/')) {
        if (action === 'create') {
            addTaskToList(task);
        } else if (action === 'update') {
            updateTaskInList(task);
        } else if (action === 'delete') {
            removeTaskFromList(task.id);
        }
    }

    else if (currentPath.includes('/tasks/') && !currentPath.includes('/update/') && !currentPath.includes('/delete/')) {
        const taskId = parseInt(currentPath.split('/tasks/')[1].replace('/', ''));
        if (taskId === task.id) {
            if (action === 'update') {
                updateTaskDetail(task);
            } else if (action === 'delete') {
                window.location.href = '/';
            }
        }
    }
}

function addTaskToList(task) {
    const taskList = document.querySelector('#task-list');
    if (!taskList) return;

    const taskCard = createTaskCard(task);

    taskList.insertAdjacentHTML('afterbegin', taskCard);

    showNotification(`Task "${task.title}" has been created`);
}

function updateTaskInList(task) {
    const taskElement = document.querySelector(`#task-${task.id}`);
    if (!taskElement) return;

    taskElement.outerHTML = createTaskCard(task);

    showNotification(`Task "${task.title}" has been updated`);
}

function removeTaskFromList(taskId) {
    const taskElement = document.querySelector(`#task-${taskId}`);
    if (!taskElement) return;

    const taskTitle = taskElement.querySelector('.card-title').textContent;

    taskElement.remove();

    showNotification(`Task "${taskTitle}" has been deleted`);
}

function updateTaskDetail(task) {
    const detailContainer = document.querySelector('#task-detail');
    if (!detailContainer) return;

    document.querySelector('#task-title').textContent = task.title;
    document.querySelector('#task-description').textContent = task.description || 'No description provided';
    document.querySelector('#task-status').textContent = task.status;
    document.querySelector('#task-created').textContent = new Date(task.created_at).toLocaleString();
    document.querySelector('#task-updated').textContent = new Date(task.updated_at).toLocaleString();

    showNotification(`Task details have been updated`);
}

function createTaskCard(task) {
    const statusClass = task.status === 'completed' ? 'task-completed' :
                       (task.status === 'in_progress' ? 'task-in-progress' : '');

    return `
    <div id="task-${task.id}" class="card ${statusClass}">
        <div class="card-body">
            <h5 class="card-title">${task.title}</h5>
            <p class="card-text">
                <span class="badge ${getStatusBadgeClass(task.status)}">${task.status}</span>
            </p>
            <div class="btn-group">
                <a href="/tasks/${task.id}/" class="btn btn-sm btn-info">
                    <i class="fas fa-eye"></i> View
                </a>
                <a href="/tasks/${task.id}/update/" class="btn btn-sm btn-warning">
                    <i class="fas fa-edit"></i> Edit
                </a>
                <a href="/tasks/${task.id}/delete/" class="btn btn-sm btn-danger">
                    <i class="fas fa-trash"></i> Delete
                </a>
                <a href="/tasks/${task.id}/email/" class="btn btn-sm btn-primary">
                    <i class="fas fa-envelope"></i> Email
                </a>
            </div>
        </div>
        <div class="card-footer text-muted">
            Last updated: ${new Date(task.updated_at).toLocaleString()}
        </div>
    </div>
    `;
}

function getStatusBadgeClass(status) {
    switch(status) {
        case 'completed':
            return 'bg-success';
        case 'in_progress':
            return 'bg-warning text-dark';
        default:
            return 'bg-secondary';
    }
}

function showNotification(message) {
    let notifContainer = document.querySelector('#notification-container');
    if (!notifContainer) {
        notifContainer = document.createElement('div');
        notifContainer.id = 'notification-container';
        notifContainer.style.position = 'fixed';
        notifContainer.style.bottom = '20px';
        notifContainer.style.right = '20px';
        notifContainer.style.zIndex = '1050';
        document.body.appendChild(notifContainer);
    }

    const notification = document.createElement('div');
    notification.className = 'toast show';
    notification.setAttribute('role', 'alert');
    notification.setAttribute('aria-live', 'assertive');
    notification.setAttribute('aria-atomic', 'true');

    notification.innerHTML = `
        <div class="toast-header">
            <strong class="me-auto">Notification</strong>
            <small>just now</small>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;

    notifContainer.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 5000);
}

document.addEventListener('DOMContentLoaded', function() {
    connectWebSocket();
});
