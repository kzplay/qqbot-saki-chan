import asyncio

import aiohttp


async def fetch_json(*urls, params=None, timeout=15):
    async def fetch(session_, url_):
        async with session_.get(url_, params=params) as response:
            return await response.json()

    if len(urls) == 1:
        url = urls[0]
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            return await fetch(session, url)
    else:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            tasks = [fetch(session, url) for url in urls]
            responses = await asyncio.gather(*tasks)
            return tuple(responses)
