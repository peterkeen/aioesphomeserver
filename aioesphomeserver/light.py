from . import BasicEntity, ListEntitiesLightResponse, LightStateResponse, LightCommandRequest

from operator import ior
from functools import reduce
from aiohttp import web
from urllib import parse

import json
from aioesphomeapi import (
    LightColorCapability,
)

class LightEntity(BasicEntity):
    DOMAIN = "light"

    def __init__(self, *args, color_modes=[LightColorCapability.ON_OFF], effects=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.supported_color_modes = color_modes
        if effects == None:
            self.effects = []
            self.effect = None
        else:
            self.effects = effects
            self.effect = effects[0]

        self.state = False
        self.brightness = 1.0
        self.color_brightness = 1.0
        self.color_temperature = 1.0
        self.cold_white = 1.0
        self.warm_white = 1.0
        self.transition_length = 0
        self.flash_length = 0
        self.color_mode = color_modes[0]
        self.red = 1.0
        self.green = 1.0
        self.blue = 1.0
        self.white = 1.0

    async def build_list_entities_response(self):
        return ListEntitiesLightResponse(
            object_id=self.object_id,
            key=self.key,
            name=self.name,
            unique_id=self.unique_id,
            supported_color_modes=self.supported_color_modes,
            effects=self.effects,
        )

    async def build_state_response(self):
        return LightStateResponse(
            key=self.key,
            state=self.state,
            brightness=self.brightness,
            color_mode=self.color_mode,
            color_brightness=self.color_brightness,
            red=self.red,
            green=self.green,
            blue=self.blue,
            white=self.white,
            color_temperature=self.color_temperature,
            cold_white=self.cold_white,
            warm_white=self.warm_white,
            effect=self.effect,

        )

    async def state_json(self):
        state = "ON" if self.state else "OFF"
        data = {
            "id": self.json_id,
            "name": self.name,
            "state": state,
            "brightness": int(self.brightness * 255),
            "color": {
                "r": self.red,
                "g": self.green,
                "b": self.green
            },
            "effects": self.effects,
            "effect": self.effect,
            "white_value": self.white
        }
        print(data)
        return json.dumps(data)

    async def set_state_from_command(self, command):
        # message LightCommandRequest {
        #   option (id) = 32;
        #   option (source) = SOURCE_CLIENT;
        #   option (ifdef) = "USE_LIGHT";
        #   option (no_delay) = true;
        #
        #   fixed32 key = 1;
        #   bool has_state = 2;
        #   bool state = 3;
        #   bool has_brightness = 4;
        #   float brightness = 5;
        #   bool has_color_mode = 22;
        #   int32 color_mode = 23;
        #   bool has_color_brightness = 20;
        #   float color_brightness = 21;
        #   bool has_rgb = 6;
        #   float red = 7;
        #   float green = 8;
        #   float blue = 9;
        #   bool has_white = 10;
        #   float white = 11;
        #   bool has_color_temperature = 12;
        #   float color_temperature = 13;
        #   bool has_cold_white = 24;
        #   float cold_white = 25;
        #   bool has_warm_white = 26;
        #   float warm_white = 27;p
        #   bool has_transition_length = 14;
        #   uint32 transition_length = 15;
        #   bool has_flash_length = 16;
        #   uint32 flash_length = 17;
        #   bool has_effect = 18;
        #   string effect = 19;
        # }

        changed = False
        for prop in ['state', 'brightness', 'white', 'effect', 'color_brightness', 'color_temperature', 'cold_white', 'warm_white', 'transition_length', 'flash_length']:
            has_prop = f"has_{prop}"
            if hasattr(command, has_prop) and getattr(command, has_prop):
                attr = getattr(command, prop)
                current_attr = getattr(self, prop)
                if attr != current_attr:
                    await self.device.log(3, self.DOMAIN, f"[{self.object_id}] Setting {prop} to {attr}")
                    setattr(self, prop, attr)
                    changed = True

        if command.has_rgb:
            if self.red != command.red:
                self.red = command.red
                changed = True

            if self.green != command.green:
                self.green = command.green
                changed = True

            if self.blue != command.blue:
                self.blue = command.blue
                changed = True

        if changed:
            await self.notify_state_change()

    async def set_state_from_query(self, state, query):
        # brightness: The brightness of the light, from 0 to 255.
        # r: The red color channel of the light, from 0 to 255.
        # g: The green color channel of the light, from 0 to 255.
        # b: The blue color channel of the light, from 0 to 255.
        # white_value: The white channel of RGBW lights, from 0 to 255.
        # flash: Flash the color provided by the other properties for a duration in seconds.
        # transition: Transition to the specified color values in this duration in seconds.
        # effect: Set an effect for the light.
        # color_temp: Set the color temperature of the light, in mireds.
        cmd = LightCommandRequest(
            has_state=True,
            state=state
        )

        for prop in ['effect']:
            if prop in query:
                setattr(cmd, f"has_{prop}", True)
                setattr(cmd, prop, query[prop][0])

        for prop in ['brightness', 'white_value']:
            if prop in query:
                setattr(cmd, f"has_{prop}", True)
                setattr(cmd, prop, float(query[prop][0]) / 255.0)

        for short_color, color in [('r', 'red'), ('g', 'green'), ('b', 'blue')]:
            if short_color in query:
                cmd.has_rgb = True
                setattr(cmd, color, float(query[short_color][0]) / 255.0)

        await self.set_state_from_command(cmd)

    async def handle(self, key, message):
        if type(message) == LightCommandRequest:
            if message.key == self.key:
                await self.set_state_from_command(message)

    async def add_routes(self, router):
        router.add_route("GET", f"/light/{self.object_id}", self.route_get_state)
        router.add_route("POST", f"/light/{self.object_id}/turn_on", self.route_turn_on)
        router.add_route("POST", f"/light/{self.object_id}/turn_off", self.route_turn_off)

    async def route_get_state(self, request):
        data = await self.state_json()
        return web.Response(text=data)

    async def route_turn_on(self, request):
        query = parse.parse_qs(request.query_string)
        await self.set_state_from_query(True, query)

        data = await self.state_json()
        return web.Response(text=data)

    async def route_turn_off(self, request):
        query = parse.parse_qs(request.query_string)
        await self.set_state_from_query(False, query)

        data = await self.state_json()
        return web.Response(text=data)
