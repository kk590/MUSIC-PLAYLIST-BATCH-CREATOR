# batch_status_tracker.py
from fastapi import APIRouter
from .redis_client import redis

router = APIRouter(prefix="/batch/jobs", tags=["batch_status_tracker"])


@router.get("/{job_id}")
async def job_status(job_id: str):
    key = f"job:{job_id}"
    status = await redis.hgetall(key)
    return {
        "state": status.get("state", "unknown"),
        "progress": status.get("progress", "0"),
    }
