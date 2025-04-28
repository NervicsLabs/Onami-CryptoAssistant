import aiohttp
import os
from dotenv import load_dotenv
from token_map.solana_token_mapping import SOLANA_TOKEN_MAPPING
import time

# Load API key
load_dotenv()
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

# Buat simple cache untuk harga
price_cache = {
    "prices": {},
    "timestamp": 0
}

async def fetch_prices_from_coingecko(token_ids):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ",".join(token_ids),
        "vs_currencies": "usd"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                return {}

async def get_cached_prices(tokens_needed):
    # Jika cache lebih lama dari 60 detik, refresh
    if time.time() - price_cache["timestamp"] > 60:
        print("⏳ Refreshing prices from CoinGecko...")
        price_data = await fetch_prices_from_coingecko([
            "solana", "usd-coin", "tether", "raydium", "bitcoin", "ethereum",
            "mango-markets", "serum", "cope", "star-atlas", "star-atlas-dao"
        ])
        price_cache["prices"] = {
            "SOL": price_data.get("solana", {}).get("usd"),
            "USDC": price_data.get("usd-coin", {}).get("usd"),
            "USDT": price_data.get("tether", {}).get("usd"),
            "RAY": price_data.get("raydium", {}).get("usd"),
            "BTC (Wrapped)": price_data.get("bitcoin", {}).get("usd"),
            "ETH (Wrapped)": price_data.get("ethereum", {}).get("usd"),
            "MNGO": price_data.get("mango-markets", {}).get("usd"),
            "SRM": price_data.get("serum", {}).get("usd"),
            "COPE": price_data.get("cope", {}).get("usd"),
            "ATLAS": price_data.get("star-atlas", {}).get("usd"),
            "POLIS": price_data.get("star-atlas-dao", {}).get("usd")
        }
        price_cache["timestamp"] = time.time()
    
    # Ambil harga hanya untuk token yang dibutuhkan
    return {token: price_cache["prices"].get(token) for token in tokens_needed}

async def fetch_wallet_balance_solana(wallet_address):
    if not HELIUS_API_KEY:
        return {"error": "Helius API Key tidak ditemukan."}

    url = f"https://api.helius.xyz/v0/addresses/{wallet_address}/balances?api-key={HELIUS_API_KEY}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

            if resp.status == 200:
                balances = data.get("tokens", [])
                native_balance_raw = data.get("nativeBalance", 0)
                fungible = {}

                # Tambahkan SOL native balance
                sol_balance = native_balance_raw / 1_000_000_000
                if sol_balance > 0:
                    fungible["SOL"] = {
                        "balance": sol_balance
                    }

                # Token fungible (non-native SOL)
                for token in balances:
                    mint = token.get("mint")
                    amount = token.get("amount", 0)
                    decimals = token.get("decimals", 0)

                    if mint and amount > 0:
                        balance = amount / (10 ** decimals)
                        token_name = SOLANA_TOKEN_MAPPING.get(mint, mint[:6] + "...")
                        fungible[token_name] = {
                            "balance": balance
                        }

                # Ambil daftar token yang perlu harga
                tokens_needed = list(fungible.keys())
                prices = await get_cached_prices(tokens_needed)

                # Formatting
                formatted_balances = {}
                total_usd = 0

                for token, info in fungible.items():
                    balance = round(info['balance'], 6)
                    usd_price = prices.get(token, None)
                    usd_value = round(balance * usd_price, 2) if usd_price else None

                    formatted_balances[token] = {
                        "balance": balance,
                        "usd": usd_value
                    }

                    if usd_value is not None:
                        total_usd += usd_value

                return {
                    "wallet_address": wallet_address,
                    "token_balances": formatted_balances,
                    "total_balance_usd": round(total_usd, 2),
                    "explorer_url": f"https://solscan.io/account/{wallet_address}"
                }
            else:
                error_message = await resp.text()
                return {"error": f"Gagal fetch data dari Solana. Status: {resp.status}. Pesan: {error_message}"}