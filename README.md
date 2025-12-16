AIO ESPHome Server
==================

Allow your Python program to show up to Home Assistant as an ESPHome device.

## Features

* Compatibility with ESPHome by using the official protocol definitions from the official `aioesphomeapi` library
* Serves the ESPHome native API as well as an HTTP server that is compatible with the official on-device web server, including the dashboard
* Fully async using asyncio
* Easy to use interface for hooking in your own entities
* Implemented ESPHome components:
  - Switch
  - Binary sensor
  - Light (no web API yet)

## Usage

```python
import asyncio

from aioesphomeserver import (
    Device,
    SwitchEntity,
)

device = Device(
    name = "Test Device",
    mac_address = "AC:BC:32:89:0E:C9",
    model = "Test Device",
    project_name = "aioesphomeserver",
    project_version = "1.0.0",
)

device.add_entity(
    SwitchEntity(
        name = "Test Switch",
    )
)

asyncio.run(device.run())
```

Now you can visit `localhost:8080` to view the web interface or add your device to Home Assistant through the ESPHome integration.

## Interfacing with your own code

Implement a listener:

```python
from aioesphomeserver import ListenerEntity, LightStatusResponse

class MyCoolListener(ListenerEntity):
    async def handle(self, key, message):
        # handle receives every message destined for the the `entity_id` specified at object creation
        # so you can basically do whatever you want

    async def modify_something(self, value):
        self.device.get_entity(self.entity_id).set_some_value(value)

#...
device.add_entity(
    MyListener(
        name="some cool listener",
        entity_id="whatever_thing"
    )
)
```

You can define methods on your listener to talk to other entities or you can retain a reference to `device` where you
have direct access to other entities as well as the ability to publish internal events.

## Status

_This is alpha quality at best._ Expect bugs, both striking and subtle. Use at your own risk.

`aioesphomeserver` currently only supports the plaintext (i.e. non-encrypted) ESPHome native protocol.
Adding the encrypted protocol is possible but because "devices" implemented with this library run on a general purpose machine rather
than a small microcontroller there are more possibilities, like using Wireguard or Tailscale.

## TODO

In rough priority order:

* [x] Finish Light web API
* [ ] Configurable ports and listening IPs
* [x] Button
* [x] Sensor
* [ ] Cover
* [ ] Zeroconf
* [ ] Fan
* [ ] Device-defined services
* [ ] Call HA defined services
* [ ] Event
* [x] TextSensor
* [ ] Number
* [ ] Select
* [ ] Date & Time & DateTime
* [ ] Valve
* [ ] MediaPlayer
* [ ] Siren
* [ ] Alarm control panel
* [ ] Camera
