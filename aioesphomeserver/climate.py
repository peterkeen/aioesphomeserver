import json
from aioesphomeapi.api_pb2 import ClimateMode, ClimateFanMode, ClimateSwingMode, ClimateAction, ClimatePreset, ClimateStateResponse, ListEntitiesClimateResponse
from . import BasicEntity, ClimateCommandRequest
from aiohttp import web
from urllib import parse

class ClimateEntity(BasicEntity):
    DOMAIN = "climate"

    def __init__(self, name, object_id, supported_modes, visual_min_temperature, visual_max_temperature, visual_target_temperature_step, **kwargs):
        super().__init__(name=name, object_id=object_id, **kwargs)
        self.supported_modes = supported_modes
        self.visual_min_temperature = visual_min_temperature
        self.visual_max_temperature = visual_max_temperature
        self.visual_target_temperature_step = visual_target_temperature_step

        # Initialize default values if they are not provided
        self.mode = kwargs.get('mode', ClimateMode.CLIMATE_MODE_OFF)
        self.target_temperature = kwargs.get('target_temperature', self.visual_min_temperature)
        self.current_temperature = kwargs.get('current_temperature', self.visual_min_temperature)
        self.fan_mode = kwargs.get('fan_mode', ClimateFanMode.CLIMATE_FAN_OFF)
        self.swing_mode = kwargs.get('swing_mode', ClimateSwingMode.CLIMATE_SWING_OFF)
        self.action = kwargs.get('action', ClimateAction.CLIMATE_ACTION_OFF)
        self.preset = kwargs.get('preset', ClimatePreset.CLIMATE_PRESET_NONE)

    async def build_list_entities_response(self):
        return ListEntitiesClimateResponse(
            object_id=self.object_id,
            key=self.key,
            name=self.name,
            unique_id=self.unique_id,
            supported_modes=self.supported_modes,
            visual_min_temperature=self.visual_min_temperature,
            visual_max_temperature=self.visual_max_temperature,
            visual_target_temperature_step=self.visual_target_temperature_step,
        )

    async def build_state_response(self):
        return ClimateStateResponse(
            key=self.key,
            mode=self.mode,
            target_temperature=self.target_temperature,
            current_temperature=self.current_temperature,
            fan_mode=self.fan_mode,
            swing_mode=self.swing_mode,
            action=self.action,
            preset=self.preset,
        )

    async def state_json(self):
        state = await self.build_state_response()
        data = {
            "mode": state.mode,
            "target_temperature": state.target_temperature,
            "current_temperature": state.current_temperature,
            "fan_mode": state.fan_mode,
            "swing_mode": state.swing_mode,
            "action": state.action,
            "preset": state.preset,
        }
        return json.dumps(data)

    async def set_state_from_command(self, command):
        changed = False
        if command.has_mode:
            self.mode = command.mode
            changed = True
        if command.has_target_temperature:
            self.target_temperature = command.target_temperature
            changed = True
        if command.has_current_temperature:
            self.current_temperature = command.current_temperature
            changed = True
        if command.has_fan_mode:
            self.fan_mode = command.fan_mode
            changed = True
        if command.has_swing_mode:
            self.swing_mode = command.swing_mode
            changed = True
        if command.has_action:
            self.action = command.action
            changed = True
        if command.has_preset:
            self.preset = command.preset
            changed = True

        if changed:
            await self.notify_state_change()

    async def set_state_from_query(self, **query):
        if 'target_temperature' in query:
            self.target_temperature = float(query['target_temperature'])
        if 'mode' in query:
            self.mode = int(query['mode'])
        if 'current_temperature' in query:
            self.current_temperature = float(query['current_temperature'])
        if 'fan_mode' in query:
            self.fan_mode = int(query['fan_mode'])
        if 'swing_mode' in query:
            self.swing_mode = int(query['swing_mode'])
        if 'action' in query:
            self.action = int(query['action'])
        if 'preset' in query:
            self.preset = int(query['preset'])

        await self.notify_state_change()

    async def handle(self, key, message):
        if isinstance(message, ClimateCommandRequest) and message.key == self.key:
            await self.set_state_from_command(message)

    async def add_routes(self, router):
        router.add_route("GET", f"/climate/{self.object_id}", self.route_get_state)
        router.add_route("POST", f"/climate/{self.object_id}/set", self.route_set_state)
        router.add_route("POST", f"/climate/{self.object_id}/set_mode", self.route_set_mode)
        router.add_route("POST", f"/climate/{self.object_id}/set_target_temperature", self.route_set_target_temperature)
        router.add_route("POST", f"/climate/{self.object_id}/set_fan_mode", self.route_set_fan_mode)
        router.add_route("POST", f"/climate/{self.object_id}/set_swing_mode", self.route_set_swing_mode)
        router.add_route("POST", f"/climate/{self.object_id}/set_preset", self.route_set_preset)

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
