# prompt_engine.py
import aiohttp
import json
import os
from dotenv import load_dotenv

# Muat file .env
load_dotenv()

# Ambil API Key dari environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

async def generate_prompt_response(data):
    # ==== PROMPT ENGINEERING YANG DITINGKATKAN ====
    prompt_text = f"""
Kamu adalah asisten crypto yang ramah dan profesional.

Riwayat percakapan sebelumnya:
{data.get('chat_history', [])}

Data baru yang diberikan:
{json.dumps(data)}

Tugas kamu:
- Jika data berisi wallet_info, buatkan ringkasan saldo wallet:
  - Sebutkan total saldo USD
  - Sebutkan 2-3 token terbesar berdasarkan nilai USD
  - Akhiri dengan ajakan ke Solscan
- Jika data berisi coin_info, buatkan ringkasan harga koin:
  - Sebutkan harga USD
  - Berikan komentar ringkas (misal \"harga saat ini stabil\" atau \"harga cukup volatil\")
- Jika data berisi query bebas, jawab dengan sopan dan relevan.
- Jawab pertanyaan atau buatkan ringkasan data wallet/harga coin
- Gunakan riwayat chat untuk menjaga konsistensi jawaban
- Jawaban maksimal 4 kalimat, sopan, ramah

Format jawaban:
- Maksimal 4 kalimat
- Bahasa profesional, ramah
- Fokus ke kebutuhan user
"""


    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={GEMINI_API_KEY}"

    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "contents": [
            {"parts": [{"text": prompt_text}]}
        ]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            result = await response.json()
            try:
                return result['candidates'][0]['content']['parts'][0]['text']
            except KeyError:
                return "Error dari Gemini API."

