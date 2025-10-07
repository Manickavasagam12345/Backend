from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import subscription, wallet
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Subscription & Wallet API - PostgreSQL + Stripe")

# CORS
origins = [
    "http://localhost:5173",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(subscription.router, prefix="/api/subscription", tags=["Subscription"])
app.include_router(wallet.router, prefix="/api/wallet", tags=["Wallet"])

@app.get("/")
def read_root():
    return {"message": "PostgreSQL + Real Stripe Integration API"}
