# batch_generator.py
from typing import List
from uuid import uuid4
from fastapi import APIRouter, Depends
from .dependencies import get_current_user
from .models import User, GenerationJob
from .tasks import generate_playlist_from_template_task

router = APIRouter(prefix="/playlists", tags=["batch_generator"])


@router.post("/batch-generate")
async def batch_generate(
    template_ids: List[str],
    current_user: User = Depends(get_current_user),
):
    job_id = str(uuid4())
    job = await GenerationJob.create(
        id=job_id,
        user_id=current_user.id,
        template_ids=template_ids,
        state="queued",
    )

    for template_id in template_ids:
        generate_playlist_from_template_task.delay(job_id=job_id, template_id=template_id, user_id=str(current_user.id))

    return {"job_id": job_id}
