"""Password Reset Module

This module handles password reset requests and confirmation.
Technologies: Redis for token storage, email service.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, validator
import secrets
import redis
import argon2

router = APIRouter()

# Redis for token storage
redis_client = redis.Redis(decode_responses=True)
TOKEN_TTL = 3600  # 1 hour

ph = argon2.PasswordHasher()


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    @validator("new_password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class ResetResponse(BaseModel):
    message: str


async def store_reset_token(email: str, token: str, ttl: int = TOKEN_TTL):
    """Store password reset token in Redis."""
    redis_client.setex(f"reset:{token}", ttl, email)


async def validate_reset_token(token: str) -> str:
    """Validate and retrieve the email for a reset token."""
    email = redis_client.get(f"reset:{token}")
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token"
        )
    return email


async def invalidate_token(token: str):
    """Invalidate a reset token after use."""
    redis_client.delete(f"reset:{token}")


async def update_password(email: str, new_password: str):
    """Update the user's password in the database."""
    from models import User

    user = await User.filter(email=email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_password = ph.hash(new_password)
    await User.filter(email=email).update(password_hash=hashed_password)

    # Invalidate all existing sessions (blacklist all tokens for this user)
    # This is optional but recommended for security
    return user


async def send_reset_email(email: str, token: str):
    """Send password reset email with the reset link."""
    try:
        import sendgrid
        sg = sendgrid.SendGridAPIClient(api_key="YOUR_SENDGRID_API_KEY")
        reset_url = f"https://app.com/reset-password?token={token}"
        # Send via SendGrid
        print(f"Reset email sent to {email}: {reset_url}")
    except ImportError:
        reset_url = f"https://app.com/reset-password?token={token}"
        print(f"SendGrid not configured. Reset URL: {reset_url}")


@router.post("/password-reset/request", response_model=ResetResponse)
async def request_reset(request_data: PasswordResetRequest):
    """Request a password reset. Always returns success to prevent email enumeration."""
    from models import User

    # Check if user exists
    user = await User.filter(email=request_data.email).first()
    if not user:
        # Still return success to prevent email enumeration attacks
        return ResetResponse(message="If email exists, reset link sent")

    # Generate token
    token = secrets.token_urlsafe(32)
    await store_reset_token(request_data.email, token, ttl=TOKEN_TTL)

    # Send reset email
    await send_reset_email(request_data.email, token)

    return ResetResponse(message="If email exists, reset link sent")


@router.post("/password-reset/confirm", response_model=ResetResponse)
async def confirm_reset(confirm_data: PasswordResetConfirm):
    """Confirm password reset with token and new password."""
    # Validate token
    email = await validate_reset_token(confirm_data.token)

    # Update password
    await update_password(email, confirm_data.new_password)

    # Invalidate the token
    await invalidate_token(confirm_data.token)

    # Blacklist any existing access tokens for this user
    # (In production, you would track tokens per user in Redis)

    return ResetResponse(message="Password updated successfully")
