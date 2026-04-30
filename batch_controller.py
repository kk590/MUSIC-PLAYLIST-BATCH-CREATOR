# batch_controller.py
from fastapi import APIRouter
from .celery_app import celery_app
from .redis_client import redis

router = APIRouter(prefix="/batch/jobs", tags=["batch_controller"])


@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str):
    celery_app.control.revoke(job_id, terminate=True)
    await redis.set(f"job:{job_id}:cancelled", "true")
    return {"status": "cancelled"}
