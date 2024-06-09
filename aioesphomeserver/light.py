from . import BasicEntity, ListEntitiesLightResponse, LightStateResponse

import json

class LightEntity(BasicEntity):
    def __init__(*args, color_modes=[], effects=[], **kwargs):
        super().__init__(*args, **kwargs)
        self.supported_color_modes = color_modes
        self.effects = effects
        
        self.effect = None        
        self.state = False
        self.brightness = 0.0
        self.color_mode = color_modes[0]
        self.color_brightness = 0.0
        self.red = 0.0
        self.green = 0.0
        self.blue = 0.0
        self.white = 0.0
        self.color_temperature = 0.0
        self.cold_white = 0.0
        self.warm_white = 0.0

    async def build_list_entities_response(self):
        return ListEntitiesLightResponse(
            object_id=self.object_id,
            key=self.key,
            name=self.name,
            unique_id=self.unique_id,
            supported_color_modes=self.color_modes,
            effects=self.effects,
        )

    async def build_state_response(self):
        return LightStateResponse(
            key=self.key,
            state=self.state,
            brightness=self.brightness,
            color_mode=self.color_mode,
            effect=self.effect,
            color_brightness=self.color_brightness,
            red=self.red,
            green=self.green,
            blue=self.blue,
            white=self.white,
            color_temperature=self.color_temperature,
            cold_white=self.cold_white,
            warm_white=self.warm_white,
        )

    async def state_json(self):
        pass

    async def set_state_from_command(self):
        pass

    async def handle(self, key, message):
        if type(message) == LightCommandRequest:
            if message.key == self.key:
                await self.set_state_from_command(message)

    async def add_routes(self, router):
        pass

