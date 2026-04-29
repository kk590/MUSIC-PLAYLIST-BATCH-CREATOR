"""User Profile Management Module

This module handles user profile updates including display name, bio,
and avatar uploads.
Technologies: Cloudinary/AWS S3 for avatar uploads, Pydantic models.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import os

router = APIRouter()


class ProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "display_name": "John Doe",
                "bio": "Music enthusiast and playlist curator",
                "avatar_url": "https://example.com/avatar.jpg"
            }
        }


class ProfileResponse(BaseModel):
    user_id: str
    email: str
    display_name: str
    bio: Optional[str]
    avatar_url: Optional[str]
    subscription_tier: str
    created_at: Optional[str]
    is_verified: bool


class AvatarUploadResponse(BaseModel):
    message: str
    avatar_url: str


# ================== STORAGE HELPERS ==================
async def upload_avatar_to_cloudinary(file: UploadFile, user_id: str) -> str:
    """Upload avatar to Cloudinary."""
    try:
        import cloudinary
        import cloudinary.uploader

        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET")
        )

        result = cloudinary.uploader.upload(
            file.file,
            folder="avatars",
            public_id=f"user_{user_id}"
        )
        return result["secure_url"]
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Cloudinary not configured"
        )


async def upload_avatar_to_s3(file: UploadFile, user_id: str) -> str:
    """Upload avatar to AWS S3."""
    try:
        import boto3

        s3 = boto3.client("s3")
        bucket = os.getenv("S3_BUCKET_NAME")
        key = f"avatars/{user_id}/{file.filename}"

        s3.upload_fileobj(
            file.file,
            bucket,
            key,
            ExtraArgs={"ContentType": file.content_type}
        )

        return f"https://{bucket}.s3.amazonaws.com/{key}"
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="AWS S3 not configured"
        )


async def upload_avatar(file: UploadFile, user_id: str, provider: str = "cloudinary") -> str:
    """Upload avatar to configured storage provider."""
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {allowed_types}"
        )

    # Validate file size (max 5MB)
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size must be less than 5MB"
        )

    if provider == "s3":
        return await upload_avatar_to_s3(file, user_id)
    else:
        return await upload_avatar_to_cloudinary(file, user_id)


# ================== ROUTES ==================
@router.patch("/profile", response_model=ProfileResponse)
async def update_profile(
    update: ProfileUpdate,
    current_user=Depends(lambda: None)  # Replace with actual auth dependency
):
    """Update user profile information."""
    from models import User

    update_data = update.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update"
        )

    user = await User.filter(id=current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await User.filter(id=current_user.id).update(**update_data)
    await user.refresh_from_db()

    return ProfileResponse(
        user_id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        bio=user.bio,
        avatar_url=user.avatar_url,
        subscription_tier=user.subscription_tier,
        created_at=str(user.created_at) if hasattr(user, "created_at") else None,
        is_verified=user.is_verified
    )


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(current_user=Depends(lambda: None)):
    """Get current user's profile."""
    from models import User

    user = await User.filter(id=current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return ProfileResponse(
        user_id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        bio=user.bio,
        avatar_url=user.avatar_url,
        subscription_tier=user.subscription_tier,
        created_at=str(user.created_at) if hasattr(user, "created_at") else None,
        is_verified=user.is_verified
    )


@router.post("/profile/avatar", response_model=AvatarUploadResponse)
async def upload_profile_avatar(
    file: UploadFile = File(...),
    current_user=Depends(lambda: None)
):
    """Upload a profile avatar image."""
    from models import User

    storage_provider = os.getenv("AVATAR_STORAGE", "cloudinary")
    avatar_url = await upload_avatar(file, str(current_user.id), storage_provider)

    await User.filter(id=current_user.id).update(avatar_url=avatar_url)

    return AvatarUploadResponse(
        message="Avatar uploaded successfully",
        avatar_url=avatar_url
    )


@router.delete("/profile/avatar", response_model=dict)
async def delete_profile_avatar(current_user=Depends(lambda: None)):
    """Remove current profile avatar."""
    from models import User

    user = await User.filter(id=current_user.id).first()
    if not user or not user.avatar_url:
        raise HTTPException(status_code=404, detail="No avatar to delete")

    # Optionally delete from storage
    # cloudinary.uploader.destroy(f"user_{user.id}")

    await User.filter(id=current_user.id).update(avatar_url=None)

    return {"message": "Avatar removed successfully"}
