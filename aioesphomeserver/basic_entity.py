from __future__ import annotations

import re
import hashlib
import socket
import logging
from zeroconf.asyncio import AsyncServiceInfo, AsyncZeroconf

class BasicEntity:
    DOMAIN = ""

    def __init__(
            self,
            name,
            object_id=None,
            unique_id=None,
            icon=None,
            device_class=None,
            entity_category=None,
    ):
        self.name = name
        self._assigned_object_id = object_id
        self._assigned_unique_id = unique_id
        self.icon = icon
        self.device_class = device_class
        self.entity_category = entity_category

        self.device = None
        self.key = None

        self._state = False

    def set_device(self, device):
        self.device = device

    def set_key(self, key):
        self.key = key

    @property
    def object_id(self):
        if self._assigned_object_id != None:
            return self._assigned_object_id
        else:
            obj_id = self.name.lower()
            obj_id = re.sub(r"\s+", "_", obj_id)
            obj_id = re.sub(r"[^\w]", "", obj_id)
            self._assigned_object_id = obj_id
            return obj_id

    @property
    def unique_id(self):
        if self._assigned_unique_id != None:
            return self._assigned_unique_id
        else:
            m = hashlib.sha256()
            m.update(self.device.name.encode())
            m.update(self.device.mac_address.encode())
            m.update(self.object_id.encode())
            m.update(self.DOMAIN.encode())
            uid = m.hexdigest()[0:16]
            self._assigned_unique_id = uid
            return uid

    @property
    def json_id(self):
        return f"{self.DOMAIN}-{self.object_id}"

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
    

    async def register_zeroconf(self, port):
        logging.info(f"Registering Zeroconf for {self.name} on port {port}")
        try:
            zeroconf = AsyncZeroconf()
            hostname = socket.gethostname()
            address = socket.gethostbyname(hostname)
            service_info = AsyncServiceInfo(
                type_="_esphomelib._tcp.local.",
                name=f"{self.name}._esphomelib._tcp.local.",
                addresses=[socket.inet_aton(address)],
                port=port,
                properties={
                    "address": address,
                    "port": str(port),
                    "api_version": "1.5.0",
                    "mac": self.mac_address,
                    "manufacturer": self.manufacturer,
                    "model": self.model,
                    "name": self.name,
                    "project_name": self.project_name,
                    "project_version": self.project_version,
                }
            )
            await zeroconf.async_register_service(service_info)
            logging.info(f"Zeroconf registration successful for {self.name} on port {port}")
            return zeroconf
        except Exception as e:
            logging.error(f"Error registering Zeroconf service for {self.name}: {e}")
            logging.exception("Exception details:")
            return None

    async def unregister_zeroconf(self, zeroconf):
        if zeroconf:
            service_info = AsyncServiceInfo(
                type_="_esphomelib._tcp.local.",
                name=f"{self.device.name}._esphomelib._tcp.local."
            )
            await zeroconf.async_unregister_service(service_info)
            await zeroconf.async_close()

