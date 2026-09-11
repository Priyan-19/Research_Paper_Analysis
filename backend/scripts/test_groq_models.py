import asyncio
import httpx
from app.core.config import settings

async def test_active():
    models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "groq/compound", "qwen/qwen3.8-27b"]
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        for m in models:
            payload = {
                "model": m,
                "messages": [{"role": "user", "content": "Say hello in one word."}],
                "max_tokens": 10
            }
            try:
                res = await client.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
                print(f"Model '{m}': Status {res.status_code}")
                if res.status_code == 200:
                    print("  RESPONSE:", res.json()['choices'][0]['message']['content'].strip())
                else:
                    print("  ERROR:", res.text[:150])
            except Exception as e:
                print(f"Model '{m}' exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_active())
