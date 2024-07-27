import asyncio
import random
import logging
import sys 
import os
import signal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aioesphomeserver import Device, ClimateEntity
from aioesphomeapi.api_pb2 import (
    ClimateMode, 
    ClimateFanMode, 
    ClimateSwingMode, 
    ClimateAction, 
    ClimatePreset,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestClimateEntity(ClimateEntity):
    def __init__(self, device, name, object_id, **kwargs):
        super().__init__(name=name, object_id=object_id, **kwargs)
        self.device = device
        self.running = True
        logger.info(f'Initialized TestClimateEntity with name {self.name}, object_id {self.object_id}')

    async def set_state_from_query(self, **kwargs):
        log_kwargs = {k: self.value_to_string(k, v) for k, v in kwargs.items()}
        logger.info(f"Received command: {log_kwargs}")
        await super().set_state_from_query(**kwargs)

    def mode_to_string(self, mode):
        return ClimateMode.Name(mode)

    def fan_mode_to_string(self, fan_mode):
        return ClimateFanMode.Name(fan_mode)

    def swing_mode_to_string(self, swing_mode):
        return ClimateSwingMode.Name(swing_mode)

    def action_to_string(self, action):
        try:
            return ClimateAction.Name(action)
        except ValueError:
            return f"UNKNOWN_ACTION_{action}"

    def preset_to_string(self, preset):
        return ClimatePreset.Name(preset)

    async def random_values(self):
        while self.running:
            try:
                changes = {}
                if random.choice([True, False]):
                    changes['target_temperature'] = round(random.uniform(self.visual_min_temperature, self.visual_max_temperature), 1)
                if random.choice([True, False]):
                    changes['mode'] = random.choice(self.supported_modes)
                if self.supports_current_temperature and random.choice([True, False]):
                    changes['current_temperature'] = round(random.uniform(self.visual_min_temperature, self.visual_max_temperature), 1)
                if self.supports_fan_mode and random.choice([True, False]):
                    changes['fan_mode'] = random.choice(self.supported_fan_modes)
                if self.supports_swing_mode and random.choice([True, False]):
                    changes['swing_mode'] = random.choice(self.supported_swing_modes)
                if self.supports_action and random.choice([True, False]):
                    changes['action'] = random.choice([ClimateAction.CLIMATE_ACTION_OFF, ClimateAction.CLIMATE_ACTION_HEATING, ClimateAction.CLIMATE_ACTION_COOLING, ClimateAction.CLIMATE_ACTION_IDLE, ClimateAction.CLIMATE_ACTION_DRYING, ClimateAction.CLIMATE_ACTION_FAN])
                if self.supports_preset and random.choice([True, False]):
                    changes['preset'] = random.choice(self.supported_presets)
                if self.supports_target_humidity and random.choice([True, False]):
                    changes['target_humidity'] = round(random.uniform(self.visual_min_humidity, self.visual_max_humidity), 1)
                if self.supports_current_humidity and random.choice([True, False]):
                    changes['current_humidity'] = round(random.uniform(self.visual_min_humidity, self.visual_max_humidity), 1)
                if self.supports_two_point_target_temperature and random.choice([True, False]):
                    changes['target_temperature_low'] = round(random.uniform(self.visual_min_temperature, self.visual_max_temperature), 1)
                    changes['target_temperature_high'] = round(random.uniform(changes['target_temperature_low'], self.visual_max_temperature), 1)

                if changes:
                    log_changes = {k: self.value_to_string(k, v) for k, v in changes.items()}
                    logger.info(f"Applying random changes: {log_changes}")
                    await self.set_state_from_query(**changes)
                
            except Exception as e:
                logger.error(f"Error in random_values: {e}", exc_info=True)

            await asyncio.sleep(random.randint(5, 15))

    def value_to_string(self, key, value):
        if key == 'mode':
            return self.mode_to_string(value)
        elif key == 'fan_mode':
            return self.fan_mode_to_string(value)
        elif key == 'swing_mode':
            return self.swing_mode_to_string(value)
        elif key == 'action':
            return self.action_to_string(value)
        elif key == 'preset':
            return self.preset_to_string(value)
        else:
            return str(value)

    def stop(self):
        self.running = False
        logger.info("Stopping random value generation")

async def main():
    device = Device(name="Test Climate", mac_address="02:01:03:22:48:01")
    climate_entity = TestClimateEntity(
        device=device,
        name="Test Climate",
        object_id="test_climate",
        supported_modes=[
            ClimateMode.CLIMATE_MODE_OFF,
            ClimateMode.CLIMATE_MODE_HEAT,
            ClimateMode.CLIMATE_MODE_COOL,
            ClimateMode.CLIMATE_MODE_AUTO,
        ],
        supports_two_point_target_temperature=True,
        visual_min_temperature=16.0,
        visual_max_temperature=30.0,
        visual_target_temperature_step=0.5,
        supports_fan_mode=True,
        supported_fan_modes=[
            ClimateFanMode.CLIMATE_FAN_ON,
            ClimateFanMode.CLIMATE_FAN_OFF,
            ClimateFanMode.CLIMATE_FAN_AUTO,
        ],
        supports_swing_mode=True,
        supported_swing_modes=[
            ClimateSwingMode.CLIMATE_SWING_OFF,
            ClimateSwingMode.CLIMATE_SWING_BOTH,
        ],
        supports_action=True,
        supports_current_temperature=True,
        supports_current_humidity=True,
        supports_target_humidity=True,
        visual_min_humidity=30,
        visual_max_humidity=80,
        supports_preset=True,
        supported_presets=[
            ClimatePreset.CLIMATE_PRESET_HOME,
            ClimatePreset.CLIMATE_PRESET_AWAY,
            ClimatePreset.CLIMATE_PRESET_BOOST,
        ],
    )
    device.add_entity(climate_entity)

    # Set initial state values after creation
    initial_state = {
        'mode': ClimateMode.CLIMATE_MODE_OFF,
        'target_temperature': 22.0,
        'target_temperature_low': 20.0,
        'target_temperature_high': 24.0,
        'current_temperature': 21.0,
        'fan_mode': ClimateFanMode.CLIMATE_FAN_AUTO,
        'swing_mode': ClimateSwingMode.CLIMATE_SWING_OFF,
        'action': ClimateAction.CLIMATE_ACTION_IDLE,
        'preset': ClimatePreset.CLIMATE_PRESET_HOME,
        'target_humidity': 50.0,
        'current_humidity': 45.0,
    }
    await climate_entity.set_state_from_query(**initial_state)

    logger.info('Starting device...')
    
    await asyncio.gather(
        device.run(api_port=6053, web_port=8081),
        climate_entity.random_values()
    )

if __name__ == "__main__":
    asyncio.run(main())