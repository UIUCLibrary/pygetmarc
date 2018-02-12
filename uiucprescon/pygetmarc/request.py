import aiohttp
import asyncio
import async_timeout


async def fetch(session, url, params):
    with async_timeout.timeout(10):
        async with session.get(url, params=params) as response:
            return await response.text(encoding="utf-8-sig")


def clean_up(data: str):
    return data.replace("\r\n", "\n")


async def get_marc_async(bib_id, validate=False):
    params = {}
    url = f"http://quest.library.illinois.edu/GetMARC/one.aspx/{bib_id}.marc"
    if validate:
        params['v'] = "true"
    async with aiohttp.ClientSession() as session:
        http = await fetch(session=session, url=url, params=params)
        return clean_up(data=http)


def get_marc(bib_id, validate=False):
    loop = asyncio.get_event_loop()
    value = loop.run_until_complete(get_marc_async(bib_id=bib_id, validate=validate))
    return value
