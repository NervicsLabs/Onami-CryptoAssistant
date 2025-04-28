import aiohttp
import os
from dotenv import load_dotenv
from wallet_checker.solana_wallet import *

# Load .env
load_dotenv()
MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

async def fetch_wallet_balance(wallet_address, chain="eth"):
    if chain == "sol":
        return await fetch_wallet_balance_solana(wallet_address)

    if not MORALIS_API_KEY:
        return {"error": "Moralis API Key tidak ditemukan."}

    if chain in ["sui"]:
        return {"error": "SUI belum tersedia. Harap tunggu update di masa depan."}

    url = f"https://deep-index.moralis.io/api/v2/wallets/{wallet_address}/balances/erc20?chain={chain}"

    headers = {
        "accept": "application/json",
        "X-API-Key": MORALIS_API_KEY
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()

                formatted = {}
                try:
                    for token in data[:100]:  # Maksimal 100 token pertama
                        symbol = token.get("symbol", None)
                        name = token.get("name", None)
                        decimals = int(token.get("decimals", 18))
                        balance_raw = int(token.get("balance", 0))
                        balance = balance_raw / (10 ** decimals)

                        # Kalau tidak ada symbol, gunakan nama
                        display_name = symbol if symbol and symbol != "UNKNOWN" else name

                        if display_name and balance > 0:
                            formatted[display_name] = balance

                    if not formatted:
                        return {
                            "wallet_address": wallet_address,
                            "message": "Wallet ini tidak memiliki token aktif yang bisa ditampilkan."
                        }
                    else:
                        sorted_tokens = dict(sorted(formatted.items(), key=lambda item: item[1], reverse=True))
                        return {
                            "wallet_address": wallet_address,
                            "token_balances": sorted_tokens
                        }
                except Exception as e:
                    return {"error": f"Gagal memproses data wallet. Error: {str(e)}"}
            else:
                error_message = await resp.text()
                return {"error": f"Gagal fetch data dari Moralis. Status: {resp.status}. Pesan: {error_message}"}