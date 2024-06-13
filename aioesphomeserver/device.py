from . import (  # type: ignore
    DeviceInfoRequest,
    DeviceInfoResponse,
)

import asyncio
import datetime

class Device:
    def __init__(
            self,
            name,
            mac_address=None,
            model=None,
            project_name=None,
            project_version=None,
            manufacturer="aioesphomeserver",
            friendly_name=None,
            suggested_area=None
    ):
        self.name = name
        self.mac_address = mac_address or self._generate_mac_address
        self.model = model
        self.project_name = project_name
        self.project_version = project_version
        self.manufacturer = manufacturer
        self.friendly_name = friendly_name
        self.suggested_area = suggested_area
        self.entities = []

    def _generate_mac_address(self):
        # https://stackoverflow.com/a/43546406
        return "02:00:00:%02x:%02x:%02x" % (random.randint(0, 255),
                                            random.randint(0, 255),
                                            random.randint(0, 255))

    async def build_device_info_response(self):
        return DeviceInfoResponse(
            uses_password = False,
            name = self.name,
            mac_address = self.mac_address,
        )

    async def log(self, level, message):
        print(f"[{datetime.datetime.now()}]({level}) {message}")
        await self.publish(None, 'log', (level, message))

    async def publish(self, publisher, key, message):
        for entity in self.entities:
            if publisher == entity:
                next
            if await entity.can_handle(key, message):
                await entity.handle(key, message)

    def add_entity(self, entity):
        entity.device = self
        entity.key = len(self.entities) + 1

        existing_entity = [e for e in self.entities if e.object_id == entity.object_id]
        if len(existing_entity) > 0:
            raise ValueError(f"Duplicate object_id: {entity.object_id}")

        self.entities.append(entity)

    def get_entity(self, object_id):
        for entity in self.entities:
            if entity.object_id == object_id:
                return entity
        return None

    def get_entity_by_key(self, key):
        if key > len(self.entities):
            return None
        return self.entities[key - 1]

    async def run(self):
        from . import NativeApiServer, WebServer

        self.add_entity(NativeApiServer(name="_server"))
        self.add_entity(WebServer(name="_web_server"))

        async with asyncio.TaskGroup() as tg:
            for entity in self.entities:
                if hasattr(entity, 'run'):
                    tg.create_task(entity.run())
