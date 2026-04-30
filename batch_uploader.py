# batch_uploader.py
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from uuid import uuid4

from .dependencies import get_current_user
from .models import User, BatchUploadJob
from .storage import upload_to_storage
from .tasks import process_metadata_task  # Celery task wrapper

router = APIRouter(prefix="/upload", tags=["batch_uploader"])


@router.post("/batch")
async def upload_files(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
):
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files uploaded")

    job_id = str(uuid4())
    job = await BatchUploadJob.create(
        id=job_id,
        user_id=current_user.id,
        filenames=[f.filename for f in files],
        state="pending",
        progress=0,
    )

    for file in files:
        content = await file.read()
        storage_path = f"{current_user.id}/{file.filename}"
        await upload_to_storage(storage_path, content)
        # Queue metadata extraction in background
        process_metadata_task.delay(user_id=str(current_user.id), file_path=storage_path, job_id=job_id)

    return {"job_id": job_id, "file_count": len(files)}
