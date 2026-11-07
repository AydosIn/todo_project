from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import TaskForm
from .models import Task


def get_user_task(request, pk):
    # Filtering by user means nobody can open someone else's task by guessing its id.
    return get_object_or_404(Task, pk=pk, user=request.user)


@login_required
def task_list(request):
    tasks = request.user.tasks.all()

    counts = {
        'all': tasks.count(),
        'active': tasks.filter(completed=False).count(),
        'completed': tasks.filter(completed=True).count(),
    }

    status = request.GET.get('status', 'all')
    if status == 'active':
        tasks = tasks.filter(completed=False)
    elif status == 'completed':
        tasks = tasks.filter(completed=True)
    else:
        status = 'all'

    q = request.GET.get('q', '').strip()
    if q:
        tasks = tasks.filter(Q(title__icontains=q) | Q(description__icontains=q))

    return render(request, 'tasks/task_list.html', {
        'tasks': tasks,
        'counts': counts,
        'status': status,
        'q': q,
    })


@login_required
def task_detail(request, pk):
    task = get_user_task(request, pk)
    return render(request, 'tasks/task_detail.html', {'task': task})


@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, f'Task "{task.title}" created.')
            return redirect('task_list')
    else:
        form = TaskForm()

    return render(request, 'tasks/task_form.html', {'form': form})


@login_required
def task_update(request, pk):
    task = get_user_task(request, pk)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated.')
            return redirect('task_detail', pk=task.pk)
    else:
        form = TaskForm(instance=task)

    return render(request, 'tasks/task_form.html', {'form': form, 'task': task})


@login_required
def task_delete(request, pk):
    task = get_user_task(request, pk)

    if request.method == 'POST':
        title = task.title
        task.delete()
        messages.success(request, f'Task "{title}" deleted.')
        return redirect('task_list')

    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


@login_required
@require_POST
def task_toggle(request, pk):
    task = get_user_task(request, pk)
    task.completed = not task.completed
    task.save(update_fields=['completed', 'updated_at'])

    next_url = request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect('task_list')
