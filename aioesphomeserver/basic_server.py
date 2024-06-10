import asyncio

from . import (
    BinarySensorEntity, 
    Device, 
    EntityListener,
    NativeApiServer,
    SwitchEntity, 
    SwitchStateResponse,
    WebServer,
    LightEntity,
)

from aioesphomeapi import LightColorCapability

class SwitchListener(EntityListener):
    async def handle(self, key, message):
        sensor = self.device.get_entity("test_esp_binary_sensor")
        if sensor != None:
            await sensor.set_state(message.state)
                
async def run_server():
    server = NativeApiServer(
        name="_server",
    )

    web_server = WebServer(
        name="_web_server",
    )

    device = Device(
        name = "Test Device",
        mac_address = "AC:BC:32:89:0E:C9",
        model = "Test Device",
        project_name = "aioesphomeserver",
        project_version = "1.0.0",
    )

    device.add_entity(server)
    device.add_entity(web_server)
    
    device.add_entity(
        BinarySensorEntity(
            name = "Test Binary Sensor",
        )
    )

    device.add_entity(
        SwitchEntity(
            name = "Test Switch",
        )
    )
    
    device.add_entity(
        SwitchListener(
            name="_listener", 
            entity_id="test_esp_switch"
        )
    )

    device.add_entity(
        LightEntity(
            name = "Text Light",
            effects = ["None", "Foo", "Bar", "Sparkle"],
            color_modes = [LightColorCapability.ON_OFF | LightColorCapability.BRIGHTNESS | LightColorCapability.RGB | LightColorCapability.WHITE],
        )
    )

    async with asyncio.TaskGroup() as tg:
        tg.create_task(server.run())
        tg.create_task(web_server.run())


asyncio.run(run_server())
