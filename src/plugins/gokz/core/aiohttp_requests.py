import aiohttp


async def aio_request(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                try:
                    return await resp.json()
                except aiohttp.ContentTypeError:
                    return await resp.text()
            else:
                return None

