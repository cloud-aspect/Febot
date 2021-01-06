"""
Utilities related to asyncio
"""

import asyncio
import json
from aiofile import AIOFile

class Timer:
    def __init__(self, timeout, callback, *args, **kwargs):
        self._timeout = timeout
        self._callback = callback
        self.args = args
        self.kwargs = kwargs
        self._task = asyncio.ensure_future(self._job())

    async def _job(self):
        await asyncio.sleep(self._timeout)
        await self._callback(*self.args, **self.kwargs)

    def cancel(self):
        self._task.cancel()

async def json_save(filepath, json_dict):
    async with AIOFile(filepath, "w+") as afp:
        await afp.write(json.dumps(json_dict, indent=2))
