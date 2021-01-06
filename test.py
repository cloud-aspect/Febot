import wrapt
from decorator import decorator
import aiohttp
import asyncio

async def fetch(session, url):
    """Execute an http call async
    Args:
        session: contexte for making the http call
        url: URL to call
    Return:
        responses: A dict like object containing http response
    """
    async with session.get(url) as response:
        return resp

async def fetch_all(cities):
    """ Gather many HTTP call made async
    Args:
        cities: a list of string 
    Return:
        responses: A list of dict like object containing http response
    """
    async with aiohttp.ClientSession() as session:
        tasks = []
        for city in cities:
            tasks.append(
                fetch(
                    session,
                    f"https://geo.api.gouv.fr/communes?nom={city}&fields=nom,region&format=json&geometry=centr",
                )
            )
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        return responses


async def run():
    response = ""
    async with aiohttp.ClientSession() as session:
        url = "https://secure.runescape.com/m=hiscore_oldschool_ironman/index_lite.ws?player=Lronic_memes"
        async with session.get(url) as response:
            response = await response.text()
            
    response = response.split(' ')
    response = [metric.split(',') for metric in response] 
    print(response)
    total = response[0][1]
    print(total)

asyncio.run(run())
