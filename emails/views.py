from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from emails.emails_utils import test_mail_protocols, check_email_pop3, check_email_imap, send_email_smtp
from emails.forms import EmailTaskForm
from tasks.models import Task


# Create your views here.
@login_required
def send_task_email(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)

    if request.method == 'POST':
        form = EmailTaskForm(request.POST)
        if form.is_valid():
            recipient = form.cleaned_data['recipient']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            attach_task_details = form.cleaned_data['attach_task_details']

            try:
                if attach_task_details:
                    # Отправка письма с деталями задачи
                    send_email_smtp(recipient, subject, message, task)
                else:
                    # Отправка обычного письма
                    send_email_smtp(recipient, subject, message)

                messages.success(request, f"Email successfully sent to {recipient}")
                return redirect('task-detail', pk=task.id)
            except Exception as e:
                messages.error(request, f"Failed to send email: {str(e)}")
    else:
        # Предзаполнение формы для нового письма
        initial_subject = f"Task: {task.title}"
        initial_message = "Here are the details of the task I wanted to share with you."
        form = EmailTaskForm(initial={
            'subject': initial_subject,
            'message': initial_message,
            'attach_task_details': True
        })

    return render(request, 'emails/send_email.html', {
        'form': form,
        'task': task
    })


@login_required
def check_emails(request):
    protocol = request.GET.get('protocol', 'imap')
    count = int(request.GET.get('count', 5))

    if protocol == 'imap':
        emails = check_email_imap(count)
        protocol_name = "IMAP"
    elif protocol == 'pop3':
        emails = check_email_pop3(count)
        protocol_name = "POP3"
    else:
        emails = []
        protocol_name = "Unknown"

    return render(request, 'emails/check_emails.html', {
        'emails': emails,
        'protocol': protocol_name,
        'count': count
    })


@login_required
def test_email_protocols(request):
    results = test_mail_protocols()
    return render(request, 'emails/test_protocols.html', {'results': results})


@login_required
def dashboard(request):
    tasks_count = Task.objects.filter(user=request.user).count()
    tasks_completed = Task.objects.filter(user=request.user, status='completed').count()
    tasks_in_progress = Task.objects.filter(user=request.user, status='in_progress').count()
    tasks_pending = Task.objects.filter(user=request.user, status='pending').count()

    mail_status = {}
    try:
        mail_status = test_mail_protocols()
    except Exception as e:
        mail_status = {'error': str(e)}

    context = {
        'tasks_count': tasks_count,
        'tasks_completed': tasks_completed,
        'tasks_in_progress': tasks_in_progress,
        'tasks_pending': tasks_pending,
        'mail_status': mail_status
    }

    return render(request, 'tasks/dashboard.html', context)
