# signals.py (Celery task signals)
from celery.signals import task_postrun

@task_postrun.connect
def notify_on_completion(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **extra):
    if state == 'SUCCESS' and task.name.startswith('batch_'):
        user_id = kwargs.get('user_id')
        job_name = task.name
        NotificationService.send(user_id, f"Batch job '{job_name}' completed successfully.")
