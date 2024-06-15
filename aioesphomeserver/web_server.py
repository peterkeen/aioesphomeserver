import asyncio
import os

from aiohttp import web
from aiohttp_sse import sse_response

from . import BasicEntity

class WebServer(BasicEntity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = asyncio.Queue()

    async def index(self, _request):
        return web.FileResponse(
            path=os.path.dirname(__file__) + '/index.html'
        )

    async def handle(self, key, message):
        if key == "state_change":
            key = message.key
            entity = self.device.get_entity_by_key(key)
            data = await entity.state_json()
            await self.queue.put(("state", data))

        if key == "log":
            await self.queue.put(("log", message))

    async def events(self, request):
        async with sse_response(request) as resp:
            for entity in self.device.entities:
                data = await entity.state_json()
                if data != None:
                    await resp.send(data, event="state")

            while resp.is_connected():
                event, data = await self.queue.get()
                if event == "log":
                    data = data[1]

                try:
                    await resp.send(data, event=event)
                except ConnectionResetError:
                    break

        return resp

    async def run(self):
        app = web.Application()
        app.router.add_route("GET", "/events", self.events)
        app.router.add_route("GET", "/", self.index)

        for entity in self.device.entities:
            await entity.add_routes(app.router)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", 8080)
        await site.start()

        while True:
            await asyncio.sleep(3600)
