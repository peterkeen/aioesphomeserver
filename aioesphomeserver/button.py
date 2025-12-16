from __future__ import annotations

import json
from aiohttp import web

from aioesphomeapi.api_pb2 import (  # type: ignore
    ListEntitiesButtonResponse,
    ButtonCommandRequest,
)

from .basic_entity import BasicEntity

class ButtonEntity(BasicEntity):
    DOMAIN = "switch"

    def __init__(
            self,
            *args,
            callback :callable =None,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.callback = callback

    
    async def build_list_entities_response(self):
        return ListEntitiesButtonResponse(
            object_id = self.object_id,
            key = self.key,
            name = self.name,
            unique_id = self.unique_id,
            icon = self.icon,
            entity_category = self.entity_category,
            device_class = self.device_class,
        )


    async def add_routes(self, router):
        router.add_route("POST", f"/button/{self.object_id}", self.route_pressed)
        router.add_route("GET", f"/button/{self.object_id}", self.route_button)
       
    async def route_button(self, request):
        return web.Response(body=
                            "<!doctype html>"
                            "<html>"
                            "<body>"
                            f"<form action=\"/button/{self.object_id}\" method=\"post\" >"
                            f"<button type=\"submit\"> {self.name}</button>"
                            "</form>"
                            "</body>"
                            "</html>",
                            content_type="text/html"
                            )

    async def route_pressed(self, request):
        await self.device.log(3, self.DOMAIN, f"[{self.object_id}] button pressed by web")
        data = {"status": "no callback function"}
        if not self.callback is None:
            self.callback()
            data = {"status": "ok"}
        return web.Response(text= json.dumps(data))

    async def handle(self, key, message):
        if type(message) == ButtonCommandRequest:
            if message.key == self.key:
                await self.device.log(3, self.DOMAIN, f"[{self.object_id}] button pressed")
                if not self.callback is None:
                    self.callback()
                #await self.set_state(message.state)
