from __future__ import annotations

import json
from aiohttp import web

from aioesphomeapi.api_pb2 import (  # type: ignore
    ListEntitiesSwitchResponse,
    SwitchCommandRequest,
    SwitchStateResponse,
)

from .basic_entity import BasicEntity

class SwitchEntity(BasicEntity):
    DOMAIN = "switch"

    def __init__(
            self,
            *args,
            assumed_state=None,
            **kwargs
    ):
        super().__init__(*args, **kwargs)

        self._state = False
    
    async def build_list_entities_response(self):
        return ListEntitiesSwitchResponse(
            object_id = self.object_id,
            key = self.key,
            name = self.name,
            unique_id = self.unique_id,
            icon = self.icon,
            entity_category = self.entity_category,
            device_class = self.device_class,
            assumed_state = self.assumed_state,
        )

    async def build_state_response(self):
        return SwitchStateResponse(
            key = self.key,
            state = await self.get_state()
        )

    async def get_state(self):
        return self._state

    async def set_state(self, val):
        await self.device.log(3, self.DOMAIN, f"[{self.object_id}] Setting state to {val}")
        old_state = self._state
        self._state = val
        if val != old_state:
            await self.notify_state_change()

    async def state_json(self):
        state = await self.get_state()
        state_str = "ON" if state else "OFF"

        data = {
            "id": self.json_id,
            "name": self.name,
            "state": state_str,
            "value": state,
        }
        return json.dumps(data)

    async def add_routes(self, router):
        router.add_route("GET", f"/switch/{self.object_id}", self.route_get_state)
        router.add_route("POST", f"/switch/{self.object_id}/turn_on", self.route_turn_on)
        router.add_route("POST", f"/switch/{self.object_id}/turn_off", self.route_turn_off)

    async def route_get_state(self, request):
        data = await self.state_json()
        return web.Response(text=data)

    async def route_turn_off(self, request):
        await self.set_state(False)
        data = await self.state_json()
        return web.Response(text=data)

    async def route_turn_on(self, request):
        await self.set_state(True)
        data = await self.state_json()
        return web.Response(text=data)

    async def handle(self, key, message):
        if type(message) == SwitchCommandRequest:
            if message.key == self.key:
                await self.set_state(message.state)
