import asyncio

from . import (
    BinarySensorEntity, 
    Device, 
    EntityListener,
    Server,
    SwitchEntity, 
    SwitchStateResponse,
)

class SwitchListener(EntityListener):
    async def handle(self, key, message):
        sensor = self.device.get_entity("test_esp_binary_sensor")
        if sensor != None:
            await sensor.set_state(message.state)
                
async def run_server():
    server = Server(
        name="_server",
        unique_id="_server",
        object_id="_server"
    )

    device = Device(
        name = "Test Device",
        mac_address = "AC:BC:32:89:0E:B9",
        model = "Test Device",
        project_name = "aioesphomeserver",
        project_version = "1.0.0",
    )

    device.add_entity(server)
    
    device.add_entity(
        BinarySensorEntity(
            object_id = "test_esp_binary_sensor",
            name = "Test Sensor",
            unique_id = "test_esp_binary_sensor"
        )
    )

    device.add_entity(
        SwitchEntity(
            object_id = "test_esp_switch",
            name = "Test Switch",
            unique_id = "test_esp_switch"
        )
    )
    
    device.add_entity(
        SwitchListener(
            name="_listener", 
            unique_id="_listener", 
            object_id="_listener",
            entity_id="test_esp_switch"
        )
    )
    
    await server.run()

asyncio.run(run_server())
