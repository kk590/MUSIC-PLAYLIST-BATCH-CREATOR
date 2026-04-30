# batch_retry_handler.py
from fastapi import APIRouter
from .tasks import get_failed_subtasks_for_job

router = APIRouter(prefix="/batch/jobs", tags=["batch_retry_handler"])


@router.post("/{job_id}/retry")
async def retry_job(job_id: str):
    failed_tasks = await get_failed_subtasks_for_job(job_id)
    retried = 0
    for task in failed_tasks:
        task.retry()
        retried += 1
    return {"retried_count": retried}
