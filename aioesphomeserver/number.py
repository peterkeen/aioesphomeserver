from __future__ import annotations

import json

from . import (
    BasicEntity,
    NumberStateResponse,
    ListEntitiesNumberResponse,
)

class NumberEntity(BasicEntity):
    DOMAIN = "number"

    def __init__(
            self,
            *args,
            min_value=None,
            max_value=None,
            step=None,
            unit_of_measurement=None,
            mode=None,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.unit_of_measurement = unit_of_measurement
        self.mode = mode
        self._state = 0.0

    async def build_list_entities_response(self):
        return ListEntitiesNumberResponse(
            object_id=self.object_id,
            name=self.name,
            key=self.key,
            unique_id=self.unique_id,
            icon=self.icon,
            min_value=self.min_value,
            max_value=self.max_value,
            step=self.step,
            unit_of_measurement=self.unit_of_measurement,
            mode=self.mode,
            entity_category=self.entity_category,
        )

    async def build_state_response(self):
        return NumberStateResponse(
            key=self.key,
            state=await self.get_state()
        )

    async def state_json(self):
        state = await self.get_state()

        data = {
            "id": self.json_id,
            "name": self.name,
            "state": state,
        }
        return json.dumps(data)

    async def get_state(self):
        return self._state

    async def set_state(self, val):
        await self.device.log(3, self.DOMAIN, f"[{self.object_id}] Setting value to {val}")
        old_state = self._state
        self._state = val
        if val != old_state:
            await self.notify_state_change()

# Example usage
if __name__ == "__main__":
    import asyncio
    import logging

    logging.basicConfig(level=logging.INFO)

    class TestDevice:
        async def log(self, level, domain, message):
            logging.log(level, message)

        async def notify_state_change(self):
            logging.info("State changed")

    async def main():
        device = TestDevice()
        number_entity = NumberEntity(
            device=device,
            name="Test Number",
            object_id="test_number",
            key=1,
            unique_id="unique_test_number",
            min_value=0.0,
            max_value=100.0,
            step=1.0,
            unit_of_measurement="%",
            mode=1,
        )

        await number_entity.set_state(50.0)
        print(await number_entity.build_list_entities_response())
        print(await number_entity.build_state_response())
        print(await number_entity.state_json())

    asyncio.run(main())
