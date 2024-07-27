from . import BasicEntity, ListEntitiesClimateResponse, ClimateStateResponse, ClimateCommandRequest
from aiohttp import web
import logging
import json
from aioesphomeapi import (
    ClimateMode,
    ClimateFanMode,
    ClimateSwingMode,
    ClimateAction,
    ClimatePreset,
)

class ClimateEntity(BasicEntity):
    DOMAIN = "climate"

    def __init__(self, *args, 
                 supported_modes=None,
                 supports_two_point_target_temperature=False,
                 visual_min_temperature=0, 
                 visual_max_temperature=100,
                 visual_target_temperature_step=0.1, 
                 supports_fan_mode=False,
                 supported_fan_modes=None,
                 supports_swing_mode=False,
                 supported_swing_modes=None,
                 supports_action=False,
                 supports_current_temperature=True,
                 supports_current_humidity=False,
                 supports_target_humidity=False,
                 visual_min_humidity=0,
                 visual_max_humidity=100,
                 supports_preset=False,
                 supported_presets=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        
        # Initialize all supported features
        self.supported_modes = supported_modes or [ClimateMode.OFF]
        self.supports_two_point_target_temperature = supports_two_point_target_temperature
        self.visual_min_temperature = visual_min_temperature
        self.visual_max_temperature = visual_max_temperature
        self.visual_target_temperature_step = visual_target_temperature_step
        self.supports_fan_mode = supports_fan_mode
        self.supported_fan_modes = supported_fan_modes or []
        self.supports_swing_mode = supports_swing_mode
        self.supported_swing_modes = supported_swing_modes or []
        self.supports_action = supports_action
        self.supports_current_temperature = supports_current_temperature
        self.supports_current_humidity = supports_current_humidity
        self.supports_target_humidity = supports_target_humidity
        self.visual_min_humidity = visual_min_humidity
        self.visual_max_humidity = visual_max_humidity
        self.supports_preset = supports_preset
        self.supported_presets = supported_presets or []

        # Initialize state values
        self.mode = self.supported_modes[0]
        self.target_temperature = visual_min_temperature
        self.target_temperature_low = visual_min_temperature
        self.target_temperature_high = visual_max_temperature
        self.current_temperature = visual_min_temperature
        self.fan_mode = self.supported_fan_modes[0] if self.supported_fan_modes else None
        self.swing_mode = self.supported_swing_modes[0] if self.supported_swing_modes else None
        self.action = ClimateAction.OFF
        self.preset = self.supported_presets[0] if self.supported_presets else None
        self.current_humidity = 0
        self.target_humidity = 0

        logging.info(f"ClimateEntity: {self.object_id} initialized")
        logging.info(f"ClimateEntity: {self.object_id} supports modes: {self.supported_modes}")
        logging.info(f"ClimateEntity: {self.object_id} supports two point target temperature: {self.supports_two_point_target_temperature}")    
        logging.info(f"ClimateEntity: {self.object_id} visual min temperature: {self.visual_min_temperature}")  
        logging.info(f"ClimateEntity: {self.object_id} visual max temperature: {self.visual_max_temperature}")
        logging.info(f"ClimateEntity: {self.object_id} visual target temperature step: {self.visual_target_temperature_step}")
        logging.info(f"ClimateEntity: {self.object_id} supports fan mode: {self.supports_fan_mode}")
        logging.info(f"ClimateEntity: {self.object_id} supported fan modes: {self.supported_fan_modes}")
        logging.info(f"ClimateEntity: {self.object_id} supports swing mode: {self.supports_swing_mode}")
        logging.info(f"ClimateEntity: {self.object_id} supported swing modes: {self.supported_swing_modes}")
        logging.info(f"ClimateEntity: {self.object_id} supports action: {self.supports_action}")
        logging.info(f"ClimateEntity: {self.object_id} supports current temperature: {self.supports_current_temperature}")
        logging.info(f"ClimateEntity: {self.object_id} supports current humidity: {self.supports_current_humidity}")
        logging.info(f"ClimateEntity: {self.object_id} supports target humidity: {self.supports_target_humidity}")
        logging.info(f"ClimateEntity: {self.object_id} visual min humidity: {self.visual_min_humidity}")
        logging.info(f"ClimateEntity: {self.object_id} visual max humidity: {self.visual_max_humidity}")
        logging.info(f"ClimateEntity: {self.object_id} supports preset: {self.supports_preset}")
        logging.info(f"ClimateEntity: {self.object_id} supported presets: {self.supported_presets}")
        logging.info(f"ClimateEntity: {self.object_id} mode: {self.mode}")
        logging.info(f"ClimateEntity: {self.object_id} target temperature: {self.target_temperature}")
        logging.info(f"ClimateEntity: {self.object_id} target temperature low: {self.target_temperature_low}")
        logging.info(f"ClimateEntity: {self.object_id} target temperature high: {self.target_temperature_high}")
        logging.info(f"ClimateEntity: {self.object_id} current temperature: {self.current_temperature}")
        logging.info(f"ClimateEntity: {self.object_id} fan mode: {self.fan_mode}")
        logging.info(f"ClimateEntity: {self.object_id} swing mode: {self.swing_mode}")
        logging.info(f"ClimateEntity: {self.object_id} action: {self.action}")
        logging.info(f"ClimateEntity: {self.object_id} preset: {self.preset}")
        logging.info(f"ClimateEntity: {self.object_id} current humidity: {self.current_humidity}")
        logging.info(f"ClimateEntity: {self.object_id} target humidity: {self.target_humidity}")
        
    async def build_list_entities_response(self):
        # Include all supported features
        return ListEntitiesClimateResponse(
            object_id=self.object_id,
            key=self.key,
            name=self.name,
            unique_id=self.unique_id,
            supported_modes=self.supported_modes,
            visual_min_temperature=self.visual_min_temperature,
            visual_max_temperature=self.visual_max_temperature,
            visual_target_temperature_step=self.visual_target_temperature_step,
            supports_two_point_target_temperature=self.supports_two_point_target_temperature,
            supported_fan_modes=self.supported_fan_modes,
            supported_swing_modes=self.supported_swing_modes,
            supports_current_temperature=self.supports_current_temperature,
            supports_action=self.supports_action,
            supports_current_humidity=self.supports_current_humidity,
            supports_target_humidity=self.supports_target_humidity,
            visual_min_humidity=self.visual_min_humidity,
            visual_max_humidity=self.visual_max_humidity,
            supported_presets=self.supported_presets,
        )

    async def build_state_response(self):
        # Include all current state values
        return ClimateStateResponse(
            key=self.key,
            mode=self.mode,
            current_temperature=self.current_temperature,
            target_temperature=self.target_temperature,
            target_temperature_low=self.target_temperature_low,
            target_temperature_high=self.target_temperature_high,
            current_humidity=self.current_humidity,
            target_humidity=self.target_humidity,
            fan_mode=self.fan_mode,
            swing_mode=self.swing_mode,
            action=self.action,
            preset=self.preset,
        )

    async def state_json(self):
        # Include all relevant state information
        state = await self.build_state_response()
        data = {
            "id": self.json_id,
            "name": self.name,
            "mode": ClimateMode(state.mode).name,
            "target_temperature": state.target_temperature,
            "current_temperature": state.current_temperature if self.supports_current_temperature else None,
            "fan_mode": ClimateFanMode(state.fan_mode).name if self.supports_fan_mode and state.fan_mode is not None else None,
            "swing_mode": ClimateSwingMode(state.swing_mode).name if self.supports_swing_mode and state.swing_mode is not None else None,
            "action": ClimateAction(state.action).name if self.supports_action else None,
            "preset": ClimatePreset(state.preset).name if self.supports_preset and state.preset is not None else None,
            "current_humidity": state.current_humidity if self.supports_current_humidity else None,
            "target_humidity": state.target_humidity if self.supports_target_humidity else None,
        }
        if self.supports_two_point_target_temperature:
            data["target_temperature_low"] = state.target_temperature_low
            data["target_temperature_high"] = state.target_temperature_high
        return json.dumps(data)

    async def set_state_from_command(self, command):
        # Handle all possible incoming commands
        changed = False
        for prop in ['mode', 'target_temperature', 'target_temperature_low', 'target_temperature_high', 'fan_mode', 'swing_mode', 'preset', 'target_humidity']:
            has_prop = f"has_{prop}"
            if hasattr(command, has_prop) and getattr(command, has_prop):
                attr = getattr(command, prop)
                current_attr = getattr(self, prop)
                if attr != current_attr:
                    await self.device.log(3, self.DOMAIN, f"[{self.object_id}] Setting {prop} to {attr}")
                    setattr(self, prop, attr)
                    changed = True

        if changed:
            await self.notify_state_change()

    async def set_state_from_query(self, **query):
        cmd = ClimateCommandRequest(key=self.key)

        if 'mode' in query:
            cmd.has_mode = True
            if isinstance(query['mode'], int):
                cmd.mode = query['mode']
            else:
                cmd.mode = ClimateMode[query['mode'].upper()]

        if 'target_temperature' in query:
            cmd.has_target_temperature = True
            cmd.target_temperature = float(query['target_temperature'])

        if self.supports_two_point_target_temperature:
            if 'target_temperature_low' in query:
                cmd.has_target_temperature_low = True
                cmd.target_temperature_low = float(query['target_temperature_low'])
            if 'target_temperature_high' in query:
                cmd.has_target_temperature_high = True
                cmd.target_temperature_high = float(query['target_temperature_high'])

        if self.supports_fan_mode and 'fan_mode' in query:
            cmd.has_fan_mode = True
            if isinstance(query['fan_mode'], int):
                cmd.fan_mode = query['fan_mode']
            else:
                cmd.fan_mode = ClimateFanMode[query['fan_mode'].upper()]

        if self.supports_swing_mode and 'swing_mode' in query:
            cmd.has_swing_mode = True
            if isinstance(query['swing_mode'], int):
                cmd.swing_mode = query['swing_mode']
            else:
                cmd.swing_mode = ClimateSwingMode[query['swing_mode'].upper()]

        if self.supports_preset and 'preset' in query:
            cmd.has_preset = True
            if isinstance(query['preset'], int):
                cmd.preset = query['preset']
            else:
                cmd.preset = ClimatePreset[query['preset'].upper()]

        if self.supports_target_humidity and 'target_humidity' in query:
            cmd.has_target_humidity = True
            cmd.target_humidity = float(query['target_humidity'])

        await self.set_state_from_command(cmd)

    async def add_routes(self, router):
        # Add routes for all supported features
        router.add_route("GET", f"/climate/{self.object_id}", self.route_get_state)
        router.add_route("POST", f"/climate/{self.object_id}/set", self.route_set_state)
        router.add_route("POST", f"/climate/{self.object_id}/set_mode", self.route_set_mode)
        router.add_route("POST", f"/climate/{self.object_id}/set_target_temperature", self.route_set_target_temperature)
        if self.supports_two_point_target_temperature:
            router.add_route("POST", f"/climate/{self.object_id}/set_target_temperature_low", self.route_set_target_temperature_low)
            router.add_route("POST", f"/climate/{self.object_id}/set_target_temperature_high", self.route_set_target_temperature_high)
        if self.supports_fan_mode:
            router.add_route("POST", f"/climate/{self.object_id}/set_fan_mode", self.route_set_fan_mode)
        if self.supports_swing_mode:
            router.add_route("POST", f"/climate/{self.object_id}/set_swing_mode", self.route_set_swing_mode)
        if self.supports_preset:
            router.add_route("POST", f"/climate/{self.object_id}/set_preset", self.route_set_preset)
        if self.supports_target_humidity:
            router.add_route("POST", f"/climate/{self.object_id}/set_target_humidity", self.route_set_target_humidity)

    # Implement the route handler methods (route_get_state, route_set_state, etc.) here
    async def route_get_state(self, request):
        data = await self.state_json()
        return web.Response(text=data)

    async def route_set_state(self, request):
        query = await request.json()
        await self.set_state_from_query(**query)
        data = await self.state_json()
        return web.Response(text=data)

    async def route_set_mode(self, request):
        query = await request.json()
        await self.set_state_from_query(mode=query.get('mode'))
        data = await self.state_json()
        return web.Response(text=data)

    async def route_set_target_temperature(self, request):
        query = await request.json()
        await self.set_state_from_query(target_temperature=query.get('target_temperature'))
        data = await self.state_json()
        return web.Response(text=data)

    async def route_set_fan_mode(self, request):
        query = await request.json()
        await self.set_state_from_query(fan_mode=query.get('fan_mode'))
        data = await self.state_json()
        return web.Response(text=data)

    async def route_set_swing_mode(self, request):
        query = await request.json()
        await self.set_state_from_query(swing_mode=query.get('swing_mode'))
        data = await self.state_json()
        return web.Response(text=data)

    async def route_set_preset(self, request):
        query = await request.json()
        await self.set_state_from_query(preset=query.get('preset'))
        data = await self.state_json()
        return web.Response(text=data)

    async def route_set_target_humidity(self, request):
        query = await request.json()
        await self.set_state_from_query(target_humidity=query.get('target_humidity'))
        data = await self.state_json()
        return web.Response(text=data)
    
    async def route_set_target_temperature_low(self, request):
        query = await request.json()
        await self.set_state_from_query(target_temperature_low=query.get('target_temperature_low'))
        data = await self.state_json()
        return web.Response(text=data)

    async def route_set_target_temperature_high(self, request):
        query = await request.json()
        await self.set_state_from_query(target_temperature_high=query.get('target_temperature_high'))
        data = await self.state_json()
        return web.Response(text=data)

    async def route_set_current_humidity(self, request):
        query = await request.json()
        await self.set_state_from_query(current_humidity=query.get('current_humidity'))
        data = await self.state_json()
        return web.Response(text=data)

    async def route_set_action(self, request):
        query = await request.json()
        await self.set_state_from_query(action=query.get('action'))
        data = await self.state_json()
        return web.Response(text=data)
