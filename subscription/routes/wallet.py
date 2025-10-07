from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import Wallet, User, Transaction, SubscriptionPlan, PaymentStatus
from schemas import WalletResponse, PaymentIntentRequest
from datetime import datetime
import stripe
import os

router = APIRouter()

# Stripe API Key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_your_key")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_your_secret")

@router.get("/{user_id}", response_model=WalletResponse)
def get_wallet_balance(user_id: str, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        user = User(user_id=user_id, email=f"{user_id}@example.com")
        db.add(user)
        db.commit()
    
    # Get or create wallet
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if not wallet:
        wallet = Wallet(user_id=user_id, balance=0.0)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    
    return wallet

@router.post("/add")
def add_money_to_wallet(
    user_id: str,
    amount: float,
    db: Session = Depends(get_db)
):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    # Get user
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        user = User(user_id=user_id, email=f"{user_id}@example.com")
        db.add(user)
        db.commit()
    
    # Update wallet
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if not wallet:
        wallet = Wallet(user_id=user_id, balance=amount)
        db.add(wallet)
    else:
        wallet.balance += amount
        wallet.updated_at = datetime.utcnow()
    
    # Log transaction
    transaction = Transaction(
        user_id=user_id,
        transaction_type="wallet_credit",
        amount=amount,
        payment_status=PaymentStatus.SUCCEEDED
    )
    db.add(transaction)
    
    db.commit()
    db.refresh(wallet)
    
    return {"status": "success", "new_balance": wallet.balance}

@router.post("/create-payment-intent")
def create_payment_intent(
    request: PaymentIntentRequest,
    db: Session = Depends(get_db)
):
    # Get plan
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.plan_id == request.plan_id
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Get wallet
    wallet = db.query(Wallet).filter(Wallet.user_id == request.user_id).first()
    wallet_balance = wallet.balance if wallet else 0.0
    
    if request.remaining_amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")
    
    try:
        # Create Stripe Payment Intent
        intent = stripe.PaymentIntent.create(
            amount=int(request.remaining_amount * 100),  # Convert to paise
            currency="inr",
            metadata={
                "user_id": request.user_id,
                "plan_id": request.plan_id,
                "wallet_used": str(wallet_balance)
            },
            automatic_payment_methods={"enabled": True}
        )
        
        # Log pending transaction
        transaction = Transaction(
            user_id=request.user_id,
            transaction_type="subscription_payment",
            amount=request.remaining_amount,
            wallet_used=wallet_balance,
            stripe_payment_intent_id=intent.id,
            plan_id=request.plan_id,
            payment_status=PaymentStatus.PENDING
        )
        db.add(transaction)
        db.commit()
        
        return {
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id
        }
    
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle payment_intent.succeeded
    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        
        user_id = payment_intent["metadata"]["user_id"]
        wallet_used = float(payment_intent["metadata"].get("wallet_used", 0))
        
        # Deduct wallet balance
        if wallet_used > 0:
            wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
            if wallet:
                wallet.balance -= wallet_used
                wallet.updated_at = datetime.utcnow()
        
        # Update transaction status
        transaction = db.query(Transaction).filter(
            Transaction.stripe_payment_intent_id == payment_intent["id"]
        ).first()
        
        if transaction:
            transaction.payment_status = PaymentStatus.SUCCEEDED
        
        db.commit()
        
        print(f"✅ Payment succeeded for user {user_id}")
    
    elif event["type"] == "payment_intent.payment_failed":
        payment_intent = event["data"]["object"]
        
        transaction = db.query(Transaction).filter(
            Transaction.stripe_payment_intent_id == payment_intent["id"]
        ).first()
        
        if transaction:
            transaction.payment_status = PaymentStatus.FAILED
            db.commit()
        
        print(f"❌ Payment failed: {payment_intent['id']}")
    
    return {"status": "success"}
