from . import BasicEntity

class EntityListener(BasicEntity):
    def __init__(self, *args, entity_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.entity_id = entity_id

    async def can_handle(self, key, message):
        if key == 'log':
            return False

        entity = self.device.get_entity(self.entity_id)
        return entity != None and message.key == entity.key

