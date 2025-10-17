import asyncio
import httpx

async def post_with_backoff(url, payload, client, max_attempts=20):
    delay = 1
    for attempt in range(max_attempts):
        try:
            r = await client.post(url, json=payload, timeout=30)
            if r.status_code == 200:
                print("Evaluation acknowledged.")
                return
        except Exception as e:
            print("Notify error:", e)
        await asyncio.sleep(delay)
        delay = min(delay * 2, 16)
    print("Failed to notify after retries.")
