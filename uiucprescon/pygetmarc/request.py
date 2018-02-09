import aiohttp
import asyncio
import async_timeout

async def fetch(session, url):
    with async_timeout.timeout(10):
        async with session.get(url) as response:
            return await response.text()


async def get_marc_async():
    async with aiohttp.ClientSession() as session:
        http = await fetch(session=session, url="http://quest.library.illinois.edu/GetMARC/one.aspx/1099891.marc")
        return http


def get_marc(bib_id):
    loop = asyncio.get_event_loop()
    value = loop.run_until_complete(get_marc_async())
    return value
