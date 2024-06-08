from __future__ import annotations

from aioesphomeapi.api_pb2 import (  # type: ignore
    ListEntitiesBinarySensorResponse,
    BinarySensorStateResponse,
)

from .basic_entity import BasicEntity

class BinarySensorEntity(BasicEntity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._state = False

    async def build_list_entities_response(self):
        return ListEntitiesBinarySensorResponse(
            object_id = self.object_id,
            name = self.name,
            unique_id = self.unique_id,
        )

    async def build_state_response(self):
        return BinarySensorStateResponse(
            state = await self.get_state()
        )

    async def get_state(self):
        return self._state

    async def set_state(self, val):
        old_state = self._state
        self._state = val
        if val != old_state:
            await self.server.notify_state_change(self)
