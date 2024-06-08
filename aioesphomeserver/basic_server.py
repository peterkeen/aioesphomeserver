import asyncio

from .server import Server
from .binary_sensor import BinarySensorEntity
from .switch import SwitchEntity

class MySwitch(SwitchEntity):
    async def on_state_change(self, old_state):
        sensor = self.server.get_entity("test_esp_binary_sensor")
        if sensor != None:
            await sensor.set_state(await self.get_state())

async def run_server():
    server = Server()
    
    server.add_entity(
        BinarySensorEntity(
            object_id = "test_esp_binary_sensor",
            name = "Test Sensor",
            unique_id = "test_esp_binary_sensor"
        )
    )

    server.add_entity(
        MySwitch(
            object_id = "test_esp_switch",
            name = "Test Switch",
            unique_id = "test_esp_switch"
        )
    )
    
    await server.run()

asyncio.run(run_server())
