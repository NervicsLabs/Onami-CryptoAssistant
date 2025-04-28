from fastapi import FastAPI
from pydantic import BaseModel
from coin_price import fetch_crypto_price
from wallet_checker.wallet_check import fetch_wallet_balance
from wallet_checker.solana_wallet import fetch_wallet_balance_solana  # <<< ini disesuaikan!
from gemini_model.gemini import generate_prompt_response
import asyncio

app = FastAPI()

# Model data untuk POST
class UserRequest(BaseModel):
    type: str
    symbol: str = None
    wallet_address: str = None
    chain: str = "eth"

# Tambahan Model khusus untuk /solana/balance
class WalletOnlyRequest(BaseModel):
    wallet_address: str

@app.get("/")
async def get():
    return {"message": "Crypto Assistant Server is Running"}

@app.post("/ask")
async def ask_question(request: UserRequest):
    if request.type == "market_info":
        price_data = await fetch_crypto_price(request.symbol)
        prompt_data = {
            "type": "market_info",
            "data": price_data
        }

    elif request.type == "portfolio_info":
        if request.chain == "sol":
            wallet_data = await fetch_wallet_balance_solana(request.wallet_address)
        else:
            wallet_data = await fetch_wallet_balance(request.wallet_address, request.chain)

        prompt_data = {
            "type": "portfolio_info",
            "data": wallet_data
        }

    else:
        return {"error": "Unknown request type."}

    reply = await generate_prompt_response(prompt_data)
    return {"reply": reply}

# ========== Ini tambahan untuk endpoint khusus Solana ==========
@app.post("/solana/balance")
async def get_solana_balance(request: WalletOnlyRequest):
    wallet_data = await fetch_wallet_balance_solana(request.wallet_address)
    return wallet_data
# ============================================================== 
