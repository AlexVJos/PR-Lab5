// WebSocket connection
let taskSocket = null;

// Initialize WebSocket connection
function connectWebSocket() {
    // Get the protocol (ws:// or wss://)
    const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';

    // Connect to WebSocket server
    taskSocket = new WebSocket(
        wsProtocol + window.location.host + '/ws/tasks/'
    );

    // Handle connection open
    taskSocket.onopen = function(e) {
        console.log('WebSocket connection established');
    };

    // Handle messages
    taskSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        console.log('WebSocket message received:', data);

        if (data.type === 'task_event') {
            handleTaskEvent(data);
        }
    };

    // Handle connection close
    taskSocket.onclose = function(e) {
        console.log('WebSocket connection closed');
        // Try to reconnect after a delay
        setTimeout(function() {
            console.log('Attempting to reconnect WebSocket...');
            connectWebSocket();
        }, 3000);
    };

    // Handle errors
    taskSocket.onerror = function(e) {
        console.error('WebSocket error:', e);
    };
}

// Handle task events (create, update, delete)
function handleTaskEvent(data) {
    const action = data.action;
    const task = data.task;

    // Different handling based on the current page
    const currentPath = window.location.pathname;

    // On task list page
    if (currentPath === '/' || currentPath.endsWith('/task-list/')) {
        if (action === 'create') {
            addTaskToList(task);
        } else if (action === 'update') {
            updateTaskInList(task);
        } else if (action === 'delete') {
            removeTaskFromList(task.id);
        }
    }

    // On task detail page
    else if (currentPath.includes('/tasks/') && !currentPath.includes('/update/') && !currentPath.includes('/delete/')) {
        const taskId = parseInt(currentPath.split('/tasks/')[1].replace('/', ''));
        if (taskId === task.id) {
            if (action === 'update') {
                updateTaskDetail(task);
            } else if (action === 'delete') {
                // Redirect to task list as the task has been deleted
                window.location.href = '/';
            }
        }
    }
}

// Add a new task to the list
function addTaskToList(task) {
    // Check if we should add this task (only if it belongs to the current user)
    // We'll handle this by checking if the element gets added to the DOM

    const taskList = document.querySelector('#task-list');
    if (!taskList) return;

    // Create a new task card
    const taskCard = createTaskCard(task);

    // Add the new task card to the list
    taskList.insertAdjacentHTML('afterbegin', taskCard);

    // Show notification
    showNotification(`Task "${task.title}" has been created`);
}

// Update an existing task in the list
function updateTaskInList(task) {
    const taskElement = document.querySelector(`#task-${task.id}`);
    if (!taskElement) return;

    // Replace the task card with the updated one
    taskElement.outerHTML = createTaskCard(task);

    // Show notification
    showNotification(`Task "${task.title}" has been updated`);
}

// Remove a task from the list
function removeTaskFromList(taskId) {
    const taskElement = document.querySelector(`#task-${taskId}`);
    if (!taskElement) return;

    // Get the task title before removing
    const taskTitle = taskElement.querySelector('.card-title').textContent;

    // Remove the task element
    taskElement.remove();

    // Show notification
    showNotification(`Task "${taskTitle}" has been deleted`);
}

// Update task details on the detail page
function updateTaskDetail(task) {
    const detailContainer = document.querySelector('#task-detail');
    if (!detailContainer) return;

    // Update the task detail fields
    document.querySelector('#task-title').textContent = task.title;
    document.querySelector('#task-description').textContent = task.description || 'No description provided';
    document.querySelector('#task-status').textContent = task.status;
    document.querySelector('#task-created').textContent = new Date(task.created_at).toLocaleString();
    document.querySelector('#task-updated').textContent = new Date(task.updated_at).toLocaleString();

    // Show notification
    showNotification(`Task details have been updated`);
}

// Create HTML for a task card
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

// Get the appropriate badge class for a status
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

// Show a notification
function showNotification(message) {
    // Create notification container if it doesn't exist
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

    // Create notification element
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

    // Add notification to container
    notifContainer.appendChild(notification);

    // Remove notification after 5 seconds
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Connect when the page loads
document.addEventListener('DOMContentLoaded', function() {
    connectWebSocket();
});
