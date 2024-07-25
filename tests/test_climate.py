import asyncio
import random
import logging
import sys 
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aioesphomeserver import Device, ClimateEntity
from aioesphomeapi.api_pb2 import ClimateMode, ClimateFanMode, ClimateSwingMode, ClimateAction, ClimatePreset

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class TestClimateEntity(ClimateEntity):
    def __init__(self, device, name, object_id, supported_modes, visual_min_temperature, visual_max_temperature, visual_target_temperature_step, **kwargs):
        super().__init__(name=name, object_id=object_id, supported_modes=supported_modes, visual_min_temperature=visual_min_temperature, visual_max_temperature=visual_max_temperature, visual_target_temperature_step=visual_target_temperature_step, **kwargs)
        self.device = device
        self.mode = ClimateMode.CLIMATE_MODE_OFF
        self.target_temperature = self.visual_min_temperature
        self.current_temperature = self.visual_min_temperature
        self.fan_mode = ClimateFanMode.CLIMATE_FAN_OFF
        self.swing_mode = ClimateSwingMode.CLIMATE_SWING_OFF
        self.action = ClimateAction.CLIMATE_ACTION_OFF
        self.preset = ClimatePreset.CLIMATE_PRESET_NONE
        logging.debug(f'Initialized TestClimateEntity with mode {self.mode}, min_temp {self.visual_min_temperature}, max_temp {self.visual_max_temperature}')

    async def random_temperature(self):
        while True:
            target_temperature = random.uniform(self.visual_min_temperature, self.visual_max_temperature)
            await self.set_state_from_query(target_temperature=target_temperature)
            await asyncio.sleep(random.randint(5, 15))

    async def random_mode(self):
        while True:
            mode = random.choice(self.supported_modes)
            await self.set_state_from_query(mode=mode)
            await asyncio.sleep(random.randint(10, 20))

    async def random_away(self):
        while True:
            away = random.choice([True, False])
            await self.set_state_from_query(away=away)
            await asyncio.sleep(random.randint(20, 30))

    async def random_values(self):
        while True:
            target_temperature = random.uniform(self.visual_min_temperature, self.visual_max_temperature)
            mode = random.choice(self.supported_modes)
            current_temperature = random.uniform(self.visual_min_temperature, self.visual_max_temperature)
            fan_mode = random.choice([ClimateFanMode.CLIMATE_FAN_OFF, ClimateFanMode.CLIMATE_FAN_ON, ClimateFanMode.CLIMATE_FAN_AUTO])
            swing_mode = random.choice([ClimateSwingMode.CLIMATE_SWING_OFF, ClimateSwingMode.CLIMATE_SWING_BOTH, ClimateSwingMode.CLIMATE_SWING_VERTICAL, ClimateSwingMode.CLIMATE_SWING_HORIZONTAL])
            action = random.choice([ClimateAction.CLIMATE_ACTION_OFF, ClimateAction.CLIMATE_ACTION_COOLING, ClimateAction.CLIMATE_ACTION_HEATING, ClimateAction.CLIMATE_ACTION_IDLE])
            preset = random.choice([ClimatePreset.CLIMATE_PRESET_NONE, ClimatePreset.CLIMATE_PRESET_HOME, ClimatePreset.CLIMATE_PRESET_AWAY])
            await self.set_state_from_query(target_temperature=target_temperature, mode=mode, current_temperature=current_temperature, fan_mode=fan_mode, swing_mode=swing_mode, action=action, preset=preset)
            await asyncio.sleep(random.randint(5, 15))

async def main():
    device = Device(name="Test Climate", mac_address="02:00:00:00:98:01")
    climate_entity = TestClimateEntity(
        device=device,
        name="Test Climate",
        object_id="test_climate",
        supported_modes=[
            ClimateMode.CLIMATE_MODE_OFF,
            ClimateMode.CLIMATE_MODE_HEAT,
            ClimateMode.CLIMATE_MODE_COOL,
            ClimateMode.CLIMATE_MODE_AUTO
        ],
        visual_min_temperature=16.0,
        visual_max_temperature=30.0,
        visual_target_temperature_step=0.5
    )
    device.add_entity(climate_entity)

    # Set initial state values after creation
    climate_entity.mode = ClimateMode.CLIMATE_MODE_OFF
    climate_entity.target_temperature = 16.0
    climate_entity.current_temperature = 16.0
    climate_entity.fan_mode = ClimateFanMode.CLIMATE_FAN_OFF
    climate_entity.swing_mode = ClimateSwingMode.CLIMATE_SWING_OFF
    climate_entity.action = ClimateAction.CLIMATE_ACTION_OFF
    climate_entity.preset = ClimatePreset.CLIMATE_PRESET_NONE

    logging.debug('Starting device...')
    await device.run(api_port=6053, web_port=8081)
    await asyncio.gather(
        climate_entity.random_temperature(),
        climate_entity.random_mode(),
        climate_entity.random_away(),
        climate_entity.random_values()
    )

if __name__ == "__main__":
    asyncio.run(main())
