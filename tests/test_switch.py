import asyncio
import logging
import random
import sys 
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aioesphomeserver import Device, SwitchEntity, LightEntity
from aioesphomeserver.light import LightCommandRequest

# Set up logging
logging.basicConfig(level=logging.INFO)

class ToggleSwitch(SwitchEntity):
    def __init__(self, name):
        super().__init__(name=name)
        self._state = False

    async def toggle(self):
        try:
            while True:
                self._state = not self._state
                logging.info(f"Toggling switch {self.name} to {'ON' if self._state else 'OFF'}")
                await self.set_state(self._state)
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            logging.warning(f"ToggleSwitch {self.name} was cancelled")
            raise

    async def set_state(self, state):
        self._state = state
        await self.device.log(3, self.DOMAIN, f"[{self.object_id}] Setting state to {state}")
        await self.notify_state_change()

class RandomDimmer(LightEntity):
    def __init__(self, name):
        super().__init__(name=name)
        self._state = False

    async def random_dimmer(self):
        try:
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
        except asyncio.CancelledError:
            logging.warning(f"RandomDimmer {self.name} was cancelled")
            raise

async def run_device(name, api_port, web_port):
    logging.info(f"Setting up {name} with API port {api_port} and Web port {web_port}")

    mac_address = f"AC:BC:32:89:0E:{api_port:02x}"

    device = Device(
        name=name,
        mac_address=mac_address,  # Ensure unique MAC address
        model="Test Device",
        project_name="aioesphomeserver",
        project_version="1.0.0",
        network="wifi",
        board="esp01_1m",
        platform="ESP8266"
    )

    test_switch = ToggleSwitch(name=f"{name} Switch")
    device.add_entity(test_switch)

    # Add a LightEntity configured as a dimmer with random changes
    dimmer = RandomDimmer(name=f"{name} Dimmer")
    device.add_entity(dimmer)

    # Run the toggle functionality
    toggle_task = asyncio.create_task(test_switch.toggle())

    # Run the random dimmer functionality
    dimmer_task = asyncio.create_task(dimmer.random_dimmer())

    try:
        # Run the device
        await device.run(api_port, web_port)
    except asyncio.CancelledError:
        logging.warning(f"Device {name} run was cancelled")
        toggle_task.cancel()
        dimmer_task.cancel()
        raise
    finally:
        await device.unregister_zeroconf()

async def main():
    devices = [
        ("Test Device 1", 6053, 8081),
        ("Test Device 2", 6054, 8082),
        ("Test Device 3", 6055, 8083),
        ("Test Device 4", 6056, 8084),
        ("Test Device 5", 6057, 8085),
        ("Test Device 6", 6058, 8086),
        ("Test Device 7", 6059, 8087),
        ("Test Device 8", 6060, 8088),
        ("Test Device 9", 6061, 8089),
        ("Test Device 10", 6062, 8090),
    ]
    await asyncio.gather(*(run_device(name, api_port, web_port) for name, api_port, web_port in devices))

if __name__ == "__main__":
    logging.info("Starting main event loop")
    try:
        asyncio.run(main())
    except asyncio.CancelledError:
        logging.info("Main event loop was cancelled")
