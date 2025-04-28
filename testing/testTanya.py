import asyncio
import requests
import aiohttp
import os
import json
from dotenv import load_dotenv
from gemini_model.gemini import generate_prompt_response
from difflib import get_close_matches

# Load .env
load_dotenv()

# Global variabel
SUPPORTED_COINS = []
COIN_ALIAS = {}

async def load_top_coins():
    global SUPPORTED_COINS, COIN_ALIAS
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "sparkline": False
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            coins = response.json()
            SUPPORTED_COINS = [coin['id'] for coin in coins]
            COIN_ALIAS = {coin['symbol']: coin['id'] for coin in coins}
            print(f"✅ Loaded {len(SUPPORTED_COINS)} top coins!")
        else:
            print(f"❌ Gagal mengambil daftar coin. Status {response.status_code}")
    except Exception as e:
        print(f"Error saat fetch coin list: {e}")

async def fetch_crypto_price(symbol):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            harga = response.json()
            return harga.get(symbol, {}).get('usd', None)
        else:
            return None
    except Exception as e:
        print(f"Error fetch harga: {e}")
        return None

async def detect_coin_in_text(text):
    text_lower = text.lower()
    # Cek langsung nama koin
    for coin in SUPPORTED_COINS:
        if coin in text_lower:
            return coin
    # Cek alias simbol
    words = text_lower.split()
    for word in words:
        if word in COIN_ALIAS:
            return COIN_ALIAS[word]
    # Kalau masih tidak ketemu, coba fuzzy match
    for word in words:
        closest = get_close_matches(word, SUPPORTED_COINS, n=1, cutoff=0.7)
        if closest:
            return closest[0]
    return None

# Memory chatting
chat_history = []

async def tanya_gemini_wallet():
    global chat_history
    print("=== Crypto Wallet Assistant (Gemini Integrated) ===")
    while True:
        user_input = input("\nTanyakan sesuatu (atau ketik 'keluar' untuk keluar): ").strip()

        if user_input.lower() == "keluar":
            print("Terima kasih telah menggunakan Crypto Assistant!")
            break

        if "wallet" in user_input or "saldo" in user_input:
            wallet_address = input("Masukkan alamat wallet Solana: ").strip()

            print("⏳ Mengambil data wallet... Mohon tunggu...")

            try:
                url = "http://localhost:8000/solana/balance"
                response = requests.post(url, json={"wallet_address": wallet_address})
                
                if response.status_code == 200:
                    wallet_data = response.json()

                    # Simpan ke history
                    chat_history.append(f"User: Cek saldo wallet {wallet_address}")
                    chat_history.append(f"Assistant: Mengambil data wallet...")

                    prompt = {
                        "chat_history": chat_history,
                        "wallet_info": wallet_data
                    }
                    jawaban = await generate_prompt_response(prompt)

                    print("\n💬 Jawaban Gemini:\n")
                    print(jawaban)

                    # Update history
                    chat_history.append(f"Assistant: {jawaban}")

                else:
                    print(f"Terjadi kesalahan: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"Error saat mengambil saldo wallet: {e}")

        elif "harga" in user_input or "price" in user_input:
            detected_coin = await detect_coin_in_text(user_input)

            if detected_coin:
                print(f"🔍 Mendeteksi koin: {detected_coin}")
                print("⏳ Mengambil harga koin... Mohon tunggu...")
                price = await fetch_crypto_price(detected_coin)

                if price is not None:
                    chat_history.append(f"User: Berapa harga {detected_coin}?")
                    chat_history.append(f"Assistant: Mengambil harga...")

                    prompt = {
                        "chat_history": chat_history,
                        "coin_info": {
                            "symbol": detected_coin,
                            "price_usd": price
                        }
                    }
                    jawaban = await generate_prompt_response(prompt)

                    print("\n💬 Jawaban Gemini:\n")
                    print(jawaban)

                    chat_history.append(f"Assistant: {jawaban}")

                else:
                    print("Gagal mengambil harga dari CoinGecko.")
            else:
                print("❌ Tidak bisa mendeteksi nama koin dalam pertanyaanmu.")

        else:
            print("⏳ Mengirim pertanyaan ke Gemini... Mohon tunggu...\n")
            try:
                chat_history.append(f"User: {user_input}")

                prompt = {
                    "chat_history": chat_history,
                    "query": user_input
                }
                jawaban = await generate_prompt_response(prompt)

                print("\n💬 Jawaban Gemini:\n")
                print(jawaban)

                chat_history.append(f"Assistant: {jawaban}")

            except Exception as e:
                print(f"Terjadi kesalahan saat tanya Gemini: {e}")

if __name__ == "__main__":
    asyncio.run(load_top_coins())  # <-- Tambahkan ini dulu!
    asyncio.run(tanya_gemini_wallet())