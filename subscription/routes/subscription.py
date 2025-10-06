from fastapi import APIRouter

router = APIRouter()

# Dummy plans
plans = [
    {"id": "basic", "name": "Basic Plan", "price": 499, "desc": "For personal use"},
    {"id": "premium", "name": "Premium Plan", "price": 999, "desc": "For small teams"},
]

@router.get("/")
async def get_subscriptions():
    return plans
