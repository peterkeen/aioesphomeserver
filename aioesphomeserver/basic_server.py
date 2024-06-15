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
    SensorEntity,
)

from aioesphomeapi import LightColorCapability

class SwitchListener(EntityListener):
    async def handle(self, key, message):
        sensor = self.device.get_entity("test_binary_sensor")
        if sensor != None:
            await sensor.set_state(message.state)

if __name__ == "__main__":
    device = Device(
        name = "Test Device",
        mac_address = "AC:BC:32:89:0E:C9",
        model = "Test Device",
        project_name = "aioesphomeserver",
        project_version = "1.0.0",
    )

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
        SensorEntity(
            name = "Test Sensor"
        )
    )

    device.add_entity(
        SwitchListener(
            name="_listener",
            entity_id="test_switch"
        )
    )

    device.add_entity(
        LightEntity(
            name = "Text Light",
            effects = ["Foo", "Bar", "Sparkle"],
            color_modes = [LightColorCapability.ON_OFF | LightColorCapability.BRIGHTNESS | LightColorCapability.RGB | LightColorCapability.WHITE],
        )
    )

    asyncio.run(device.run())
