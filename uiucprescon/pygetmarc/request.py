import typing

import aiohttp
import asyncio
import async_timeout


async def fetch(session: aiohttp.ClientSession, url: str, params: typing.Dict[str, str]) -> typing.Any:
    with async_timeout.timeout(10):
        async with session.get(url, params=params) as response:
            return await response.text(encoding="utf-8-sig")


def clean_up(data: str) -> str:
    # fix each line so that it has the proper line endings
    lines = []
    for i, line in enumerate(data.splitlines()):
        # remove any Processing Instruction
        if "<?" in line:
            continue
        lines.append(line)

    return "\n".join(lines)


async def get_marc_async(bib_id: typing.Union[int, str], validate: bool = False) -> str:
    params = {}
    url = f"http://quest.library.illinois.edu/GetMARC/one.aspx/{bib_id}.marc"

    if validate:
        params['v'] = "true"

    async with aiohttp.ClientSession() as session:
        http = await fetch(session=session, url=url, params=params)
        cleaned_up_data = clean_up(data=http)
        return cleaned_up_data


def get_marc(bib_id: typing.Union[int, str], validate: bool = False) -> str:
    """
    Get the marc data from a giving bib_id

    Args:
        bib_id: The bib id from a Voyager record
        validate: MARC XML returned from the Z39.50 target should be validated against the XML schema before further
        processing.

    Returns: Marc XML data

    """
    loop = asyncio.get_event_loop()
    value = loop.run_until_complete(get_marc_async(bib_id=bib_id, validate=validate))
    return value
