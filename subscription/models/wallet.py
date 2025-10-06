# models/wallet.py
from pydantic import BaseModel

class Wallet(BaseModel):
    user_id: str
    balance: float
