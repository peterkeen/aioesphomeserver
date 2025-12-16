from __future__ import annotations

import json

from . import (
    BasicEntity,
    TextSensorStateResponse,
    ListEntitiesTextSensorResponse,
)

class TextSensorEntity(BasicEntity):
    DOMAIN = "text_sensor"

    def __init__(
            self,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._state = ""

    async def build_list_entities_response(self):
        return ListEntitiesTextSensorResponse(
            object_id = self.object_id,
            name = self.name,
            key = self.key,
            unique_id = self.unique_id,
            icon = self.icon,
            device_class = self.device_class,
            entity_category = self.entity_category,
        )

    async def build_state_response(self):
        return TextSensorStateResponse(
            key = self.key,
            state = await self.get_state()
        )

    async def state_json(self):
        state = await self.get_state()

        data = {
            "id": self.json_id,
            "name": self.name,
            "state": state,
            "value": state,
        }
        return json.dumps(data)

    async def get_state(self):
        return self._state

    async def set_state(self, val):
        old_state = self._state
        self._state = val
        if val != old_state:
            await self.device.log(3, self.DOMAIN, f"[{self.object_id}] Setting value to {val}")
            await self.notify_state_change()
