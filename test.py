import asyncio
import aiohttp
import time
import nest_asyncio

async def fetch(session, url):
    try:
        async with session.get(url) as response:
            return await response.text()
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

async def run_load_test(url, num_requests):
    connector = aiohttp.TCPConnector(limit=20)  # Prevent overloading server
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch(session, url) for _ in range(num_requests)]
        start = time.perf_counter()
        responses = await asyncio.gather(*tasks)
        end = time.perf_counter()
        
        success = sum(1 for r in responses if r is not None)
        print(f"Completed {success}/{num_requests} requests in {end - start:.2f}s")
        print(f"Average time: {(end - start)/num_requests:.4f}s")
        print(f"Requests/sec: {num_requests/(end - start):.2f}")

if __name__ == "__main__":
    nest_asyncio.apply()  # Only needed in Jupyter notebooks
    url = "http://127.0.0.1:8000/search/?source=NDLS&dest=BCT&date=2025-04-25&allow_connect=1"
    asyncio.run(run_load_test(url, 1000))
