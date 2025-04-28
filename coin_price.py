import aiohttp

async def fetch_crypto_price(symbol="bitcoin"):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return {
                "symbol": symbol,
                "price_usd": data.get(symbol, {}).get("usd", "N/A")
            }