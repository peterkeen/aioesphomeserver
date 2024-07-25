import asyncio
import logging
import random
import sys 
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aioesphomeserver import Device, LightEntity, LightCommandRequest
from aioesphomeapi import LightColorCapability

# Set up logging
logging.basicConfig(level=logging.INFO)

class RandomDimmer(LightEntity):
    def __init__(self, name):
        super().__init__(name=name, color_modes=[LightColorCapability.BRIGHTNESS])

    async def random_dimmer(self):
        while True:
            brightness = random.uniform(0, 1)  # Set brightness as a float between 0 and 1
            logging.info(f"Setting dimmer {self.name} brightness to {brightness * 100:.2f}%")
            command = LightCommandRequest(
                key=self.key,
                has_state=True,
                state=True,
                has_brightness=True,
                brightness=brightness
            )
            await self.set_state_from_command(command)
            await asyncio.sleep(5)

    async def handle(self, key, message):
        if isinstance(message, LightCommandRequest):
            if message.key == self.key:
                logging.info(f"Received command for {self.name}: {message}")
                await self.set_state_from_command(message)

async def run_device(name, api_port, web_port):
    logging.info(f"Setting up {name} with API port {api_port} and Web port {web_port}")

    mac_address = f"AC:BC:32:89:0E:{api_port:02x}"

    device = Device(
        name=name,
        mac_address=mac_address,
        model="Test Device",
        project_name="aioesphomeserver",
        project_version="1.0.0",
        network="wifi",
        board="esp01_1m",
        platform="ESP8266"
    )

    # Add a LightEntity configured as a dimmer with random changes
    dimmer = RandomDimmer(name=f"{name} Dimmer")
    device.add_entity(dimmer)

    # Run the random dimmer functionality
    asyncio.create_task(dimmer.random_dimmer())

    try:
        # Run the device
        await device.run(api_port, web_port)
    finally:
        await device.unregister_zeroconf()

async def main():
    # Define a single device
    name, api_port, web_port = "Test Device", 6053, 8081
    await run_device(name, api_port, web_port)

if __name__ == "__main__":
    logging.info("Starting main event loop")
    asyncio.run(main())
