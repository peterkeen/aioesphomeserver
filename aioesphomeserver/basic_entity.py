from __future__ import annotations

class BasicEntity:
    def __init__(self, object_id, name, unique_id):
        self.device = None
        self.key = None
        self.object_id = object_id
        self.name = name
        self.unique_id = unique_id

        self._state = False

    def set_device(self, device):
        self.device = device

    def set_key(self, key):
        self.key = key

    async def build_list_entities_response(self):
        pass

    async def build_state_response(self):
        pass

    async def state_json(self):
        pass

    async def can_handle(self, key, message):
        return True

    async def handle(self, key, message):
        pass

    async def add_routes(self, router):
        pass

    async def notify_state_change(self):
        await self.device.publish(
            self, 
            'state_change', 
            await self.build_state_response()
        )
    
