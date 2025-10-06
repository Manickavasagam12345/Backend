from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import subscription, wallet

app = FastAPI(title="Subscription & Wallet API")

# CORS
origins = ["http://localhost:5173"]  # React dev server
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
