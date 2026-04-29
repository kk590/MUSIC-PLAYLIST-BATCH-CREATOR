"""Subscription Tiers Module

This module handles subscription tier management and Stripe/Paddle integration.
Technologies: Stripe/Paddle, webhook handling for payment confirmation.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Literal
from enum import Enum
import os

router = APIRouter()


class SubscriptionTier(str, Enum):
    FREE = "free"
    PREMIUM = "premium"


class SubscriptionResponse(BaseModel):
    tier: str
    checkout_url: Optional[str] = None
    message: str
    is_active: bool


class WebhookEvent(BaseModel):
    type: str
    data: dict


# ================== STRIPE INTEGRATION ==================
async def create_stripe_checkout(user_id: str, email: str, tier: SubscriptionTier) -> dict:
    """Create a Stripe checkout session for subscription."""
    try:
        import stripe

        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

        price_id = os.getenv(
            "STRIPE_PREMIUM_PRICE_ID"
        )  # Configure in environment

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"https://app.com/subscription/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url="https://app.com/subscription/cancel",
            client_reference_id=str(user_id),
            customer_email=email,
            metadata={"tier": tier.value, "user_id": str(user_id)}
        )

        return {"checkout_url": session.url, "session_id": session.id}
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Stripe SDK not available"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Stripe error: {str(e)}"
        )


async def handle_stripe_webhook(request: Request) -> dict:
    """Handle Stripe webhook for payment confirmation."""
    try:
        import stripe

        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")

        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            user_id = session.get("metadata", {}).get("user_id")

            if user_id:
                from models import User
                await User.filter(id=user_id).update(subscription_tier="premium")

        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")


# ================== PADDLE INTEGRATION ==================
async def create_paddle_checkout(user_id: str, email: str, tier: SubscriptionTier) -> dict:
    """Create a Paddle checkout for subscription."""
    try:
        from paddle_billing import Client

        paddle = Client(api_key=os.getenv("PADDLE_API_KEY"))

        transaction = paddle.transactions.create(
            items=[{
                "price_id": os.getenv("PADDLE_PREMIUM_PRICE_ID"),
                "quantity": 1
            }],
            customer_email_address=email,
            custom_data={"user_id": str(user_id), "tier": tier.value}
        )

        return {"checkout_url": transaction.details_url, "transaction_id": transaction.id}
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Paddle SDK not available"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Paddle error: {str(e)}"
        )


# ================== ROUTES ==================
@router.post("/subscribe", response_model=SubscriptionResponse)
async def subscribe(
    tier: SubscriptionTier,
    payment_provider: Literal["stripe", "paddle"] = "stripe",
    current_user=Depends(lambda: None)
):
    """Subscribe to a tier (FREE or PREMIUM)."""
    from models import User

    user = await User.filter(id=current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if tier == SubscriptionTier.FREE:
        # Downgrade to free
        await User.filter(id=current_user.id).update(subscription_tier="free")
        return SubscriptionResponse(
            tier="free",
            message="Subscription downgraded to free tier",
            is_active=False
        )

    # Create checkout for premium
    if payment_provider == "stripe":
        checkout = await create_stripe_checkout(
            str(current_user.id),
            user.email,
            tier
        )
        return SubscriptionResponse(
            tier="premium",
            checkout_url=checkout["checkout_url"],
            message="Proceed to Stripe checkout",
            is_active=False
        )
    else:
        checkout = await create_paddle_checkout(
            str(current_user.id),
            user.email,
            tier
        )
        return SubscriptionResponse(
            tier="premium",
            checkout_url=checkout["checkout_url"],
            message="Proceed to Paddle checkout",
            is_active=False
        )


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(current_user=Depends(lambda: None)):
    """Get current user's subscription status."""
    from models import User

    user = await User.filter(id=current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return SubscriptionResponse(
        tier=user.subscription_tier,
        message="Current subscription",
        is_active=user.subscription_tier == "premium"
    )


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Stripe webhook endpoint for payment events."""
    return await handle_stripe_webhook(request)
