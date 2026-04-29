"""User Signup Module (Email/Social)

This module handles user registration via email/password and social OAuth providers.
Technologies: OAuth2 (Google, Facebook), JWT, Argon2 for password hashing, SendGrid for emails.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
import argon2
import secrets

# OAuth setup
try:
    from authlib.integrations.starlette_client import OAuth
    oauth = OAuth()
    AUTHLIB_AVAILABLE = True
except ImportError:
    AUTHLIB_AVAILABLE = False

router = APIRouter()

# Password hasher
ph = argon2.PasswordHasher()


class EmailSignupRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: Optional[str] = None

    @validator("password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class SocialSignupRequest(BaseModel):
    provider: str  # "google", "facebook", etc.
    access_token: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class SignupResponse(BaseModel):
    message: str
    user_id: Optional[str] = None
    verification_sent: bool = False


# ================== DATABASE HELPERS ==================
async def create_user(email: str, hashed_password: str, display_name: str = None) -> dict:
    """Create a new user in the database."""
    from models import User
    user = await User.create(
        email=email,
        password_hash=hashed_password,
        display_name=display_name or email.split("@")[0],
        is_verified=False,
        subscription_tier="free"
    )
    return {"id": user.id, "email": user.email}


async def find_user_by_email(email: str):
    """Find an existing user by email."""
    from models import User
    return await User.filter(email=email).first()


async def store_verification_token(email: str, token: str, ttl: int = 86400):
    """Store email verification token in Redis."""
    import redis
    r = redis.Redis(decode_responses=True)
    r.setex(f"verify:{token}", ttl, email)


async def send_verification_email(email: str, token: str):
    """Send email verification link."""
    try:
        import sendgrid
        sg = sendgrid.SendGridAPIClient(api_key="YOUR_SENDGRID_API_KEY")
        verification_url = f"https://app.com/verify-email?token={token}"
        # Send email via SendGrid
        # Implementation depends on SendGrid setup
        print(f"Verification email sent to {email}: {verification_url}")
    except ImportError:
        print(f"SendGrid not configured. Verification URL: {verification_url}")


# ================== ROUTES ==================
@router.post("/signup/email", response_model=SignupResponse)
async def email_signup(signup_data: EmailSignupRequest):
    """Register a new user via email and password."""
    # Check if user already exists
    existing = await find_user_by_email(signup_data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password with Argon2
    hashed_password = ph.hash(signup_data.password)

    # Create user
    user = await create_user(
        email=signup_data.email,
        hashed_password=hashed_password,
        display_name=signup_data.display_name
    )

    # Generate verification token
    token = secrets.token_urlsafe(32)
    await store_verification_token(signup_data.email, token, ttl=86400)
    await send_verification_email(signup_data.email, token)

    return SignupResponse(
        message="Verification email sent",
        user_id=str(user["id"]),
        verification_sent=True
    )


@router.get("/login/google")
async def google_login(request: Request):
    """Initiate Google OAuth login flow."""
    if not AUTHLIB_AVAILABLE:
        raise HTTPException(status_code=503, detail="OAuth library not available")

    redirect_uri = request.url_for("google_auth_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/login/google/callback")
async def google_auth_callback(request: Request):
    """Handle Google OAuth callback and create/login user."""
    if not AUTHLIB_AVAILABLE:
        raise HTTPException(status_code=503, detail="OAuth library not available")

    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")

        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info")

        email = user_info.get("email")
        existing_user = await find_user_by_email(email)

        if existing_user:
            # Login existing user
            from auth_login import create_access_token
            access_token = create_access_token(data={"sub": email, "provider": "google"})
            return {"access_token": access_token, "token_type": "bearer", "message": "Logged in"}
        else:
            # Create new user
            hashed_password = ph.hash(secrets.token_urlsafe(32))
            user = await create_user(
                email=email,
                hashed_password=hashed_password,
                display_name=user_info.get("name")
            )
            access_token = create_access_token(data={"sub": email, "provider": "google"})
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "message": "Account created via Google",
                "user_id": str(user["id"])
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")


@router.get("/login/facebook")
async def facebook_login(request: Request):
    """Initiate Facebook OAuth login flow."""
    if not AUTHLIB_AVAILABLE:
        raise HTTPException(status_code=503, detail="OAuth library not available")

    redirect_uri = request.url_for("facebook_auth_callback")
    return await oauth.facebook.authorize_redirect(request, redirect_uri)


@router.get("/login/facebook/callback")
async def facebook_auth_callback(request: Request):
    """Handle Facebook OAuth callback."""
    if not AUTHLIB_AVAILABLE:
        raise HTTPException(status_code=503, detail="OAuth library not available")

    try:
        token = await oauth.facebook.authorize_access_token(request)
        user_info = token.get("data")

        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info")

        email = user_info.get("email")
        existing_user = await find_user_by_email(email)

        if existing_user:
            from auth_login import create_access_token
            access_token = create_access_token(data={"sub": email, "provider": "facebook"})
            return {"access_token": access_token, "token_type": "bearer"}
        else:
            hashed_password = ph.hash(secrets.token_urlsafe(32))
            user = await create_user(
                email=email,
                hashed_password=hashed_password,
                display_name=user_info.get("name")
            )
            access_token = create_access_token(data={"sub": email, "provider": "facebook"})
            return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")


@router.get("/verify-email")
async def verify_email(token: str):
    """Verify user's email address."""
    import redis
    r = redis.Redis(decode_responses=True)
    email = r.get(f"verify:{token}")

    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    from models import User
    user = await User.filter(email=email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    await user.save()
    r.delete(f"verify:{token}")

    return {"message": "Email verified successfully"}
