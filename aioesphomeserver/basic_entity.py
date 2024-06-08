from __future__ import annotations

class BasicEntity:
    def __init__(self, object_id, name, unique_id):
        self.server = None
        self.object_id = object_id
        self.name = name
        self.unique_id = unique_id

        self._state = False

    def set_server(self, server):
        self.server = server

    async def build_list_entities_response(self):
        pass

    async def build_state_response(self):
        pass

    async def handle(self, message):
        pass
    
