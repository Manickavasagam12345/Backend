from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import SubscriptionPlan, UserSubscription, User
from schemas import SubscriptionPlanResponse, SubscriptionActivation
from typing import List
from datetime import datetime

router = APIRouter()

@router.get("/", response_model=List[SubscriptionPlanResponse])
def get_subscription_plans(db: Session = Depends(get_db)):
    plans = db.query(SubscriptionPlan).all()
    
    # If no plans exist, create default ones
    if not plans:
        default_plans = [
            SubscriptionPlan(
                plan_id="basic",
                name="Basic Plan",
                price=499.0,
                description="For personal use"
            ),
            SubscriptionPlan(
                plan_id="premium",
                name="Premium Plan",
                price=999.0,
                description="For small teams"
            ),
            SubscriptionPlan(
                plan_id="enterprise",
                name="Enterprise Plan",
                price=2499.0,
                description="For large teams"
            )
        ]
        db.add_all(default_plans)
        db.commit()
        plans = db.query(SubscriptionPlan).all()
    
    return plans

@router.post("/activate")
def activate_subscription(
    activation: SubscriptionActivation,
    db: Session = Depends(get_db)
):
    # Find plan by plan_id
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.plan_id == activation.plan_id
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Check if user exists, if not create
    user = db.query(User).filter(User.user_id == activation.user_id).first()
    if not user:
        user = User(user_id=activation.user_id, email=f"{activation.user_id}@example.com")
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Create subscription
    subscription = UserSubscription(
        user_id=activation.user_id,
        plan_id=plan.id,
        payment_method=activation.payment_method,
        status="active",
        activated_at=datetime.utcnow()
    )
    
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    
    return {
        "status": "success",
        "message": "Subscription activated",
        "subscription": {
            "plan_name": plan.name,
            "price": plan.price,
            "activated_at": subscription.activated_at
        }
    }

@router.get("/user/{user_id}")
def get_user_subscription(user_id: str, db: Session = Depends(get_db)):
    subscription = db.query(UserSubscription).filter(
        UserSubscription.user_id == user_id,
        UserSubscription.status == "active"
    ).first()
    
    if not subscription:
        return {"subscription": None}
    
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == subscription.plan_id
    ).first()
    
    return {
        "subscription": {
            "plan_name": plan.name,
            "price": plan.price,
            "status": subscription.status,
            "activated_at": subscription.activated_at
        }
    }
