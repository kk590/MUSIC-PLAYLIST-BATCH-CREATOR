# template_manager.py
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from .dependencies import get_current_user
from .models import Template, User

router = APIRouter(prefix="/templates", tags=["template_manager"])


class PlaylistTemplate(BaseModel):
    name: str
    rules: List[Dict]
    duration_minutes: Optional[int] = None


@router.post("")
async def create_template(
    template: PlaylistTemplate,
    current_user: User = Depends(get_current_user),
):
    db_template = await Template.create(
        name=template.name,
        rules=template.rules,
        duration_minutes=template.duration_minutes,
        user_id=current_user.id,
    )
    return db_template
