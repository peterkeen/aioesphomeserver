from . import (  # type: ignore
    DeviceInfoRequest,
    DeviceInfoResponse,
)

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
