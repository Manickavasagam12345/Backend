from fastapi import APIRouter

router = APIRouter()

# Dummy wallet (user_id -> balance)
wallets = {
    "user1": 1500
}

@router.get("/{user_id}")
async def get_wallet(user_id: str):
    return {"balance": wallets.get(user_id, 0)}

@router.post("/pay")
async def pay_with_wallet(user_id: str, plan_id: str):
    # Dummy plans
    plans = {
        "basic": 499,
        "premium": 999
    }

    if plan_id not in plans:
        return {"status": "failed", "error": "Invalid plan"}

    plan_price = plans[plan_id]
    current_balance = wallets.get(user_id, 0)

    if current_balance >= plan_price:
        wallets[user_id] = current_balance - plan_price
        return {"status": "success", "new_balance": wallets[user_id]}
    else:
        return {"status": "failed", "error": "Insufficient balance"}
