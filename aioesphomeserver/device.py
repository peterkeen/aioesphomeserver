from . import (
    DeviceInfoRequest,
    DeviceInfoResponse,
)

from .logger import format_log

from inspect import getframeinfo, stack

import asyncio
import socket
import re
import random
import logging
from zeroconf.asyncio import AsyncZeroconf
from zeroconf import ServiceInfo

logger = logging.getLogger(__name__)

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
            suggested_area=None,
            network=None,
            board=None,
            platform=None
    ):
        self.name = name
        self.mac_address = mac_address or self._generate_mac_address()
        self.model = model
        self.project_name = project_name
        self.project_version = project_version
        self.manufacturer = manufacturer
        self.friendly_name = friendly_name
        self.suggested_area = suggested_area
        self.network = network
        self.board = board
        self.platform = platform
        self.entities = []
        self.zeroconf = None
        self.service_info = None
        self.running = True
        self.api_port = None
        self.web_port = None

    def _generate_mac_address(self):
        return "02:00:00:%02x:%02x:%02x" % (random.randint(0, 255),
                                            random.randint(0, 255),
                                            random.randint(0, 255))

    def _get_ip_address(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.254.254.254', 1))
            ip_address = s.getsockname()[0]
        except Exception:
            ip_address = '127.0.0.1'
        finally:
            s.close()
        return ip_address
    
    def get_ip_address(self):
        return self._get_ip_address()

    async def build_device_info_response(self):
        return DeviceInfoResponse(
            uses_password=False,
            name=self.name,
            mac_address=self.mac_address,
        )

    async def log(self, level, tag, message):
        caller = getframeinfo(stack()[1][0])
        formatted_log = format_log(level, tag, caller.lineno, message)
        print(formatted_log)
        try:
            await self.publish(None, 'log', (level, formatted_log))
        except Exception as e:
            logger.error(f"Error publishing log: {e}", exc_info=True)

    async def publish(self, publisher, key, message):
        for entity in self.entities:
            if publisher == entity:
                continue
            try:
                if await entity.can_handle(key, message):
                    await entity.handle(key, message)
            except ConnectionResetError:
                logger.warning(f"Connection reset while publishing to {entity.name}")
            except Exception as e:
                logger.error(f"Error publishing to {entity.name}: {e}", exc_info=True)

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

    async def run(self, api_port, web_port):
        from . import NativeApiServer, WebServer

        self.api_port = api_port
        self.web_port = web_port

        self.add_entity(NativeApiServer(name="_server", port=self.api_port))
        self.add_entity(WebServer(name="_web_server", port=self.web_port))

        while self.running:
            try:
                self.zeroconf = await self.register_zeroconf(self.api_port)

                async with asyncio.TaskGroup() as tg:
                    for entity in self.entities:
                        if hasattr(entity, 'run'):
                            tg.create_task(entity.run())

                    tg.create_task(self.heartbeat())

            except ConnectionResetError:
                logger.warning("Connection reset. Restarting servers in 5 seconds...")
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                logger.info("Device run cancelled. Shutting down...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in device run: {e}", exc_info=True)
                await asyncio.sleep(5)

        await self.shutdown()

    async def heartbeat(self):
        while self.running:
            try:
                for entity in self.entities:
                    if hasattr(entity, 'check_connection'):
                        await entity.check_connection()
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
            except Exception as e:
                logger.error(f"Error in heartbeat: {e}", exc_info=True)

    async def shutdown(self):
        self.running = False
        for entity in self.entities:
            if hasattr(entity, 'stop'):
                await entity.stop()
        await self.unregister_zeroconf()

    async def register_zeroconf(self, port):
        try:
            zeroconf = AsyncZeroconf()
            service_type = "_esphomelib._tcp.local."
            
            sanitized_name = re.sub(r'[^a-zA-Z0-9]', '_', self.name).lower()
            
            service_name = f"{sanitized_name}.{service_type}"
            ip_address = self._get_ip_address()
            hostname = f"{sanitized_name}.local."

            service_info = ServiceInfo(
                service_type,
                service_name,
                addresses=[socket.inet_aton(ip_address)],
                port=port,
                properties={
                    "network": self.network or "wifi",
                    "board": self.board or "esp01_1m",
                    "platform": self.platform or "ESP8266",
                    "mac": self.mac_address.replace(":", "").lower(),
                    "version": self.project_version,
                    "friendly_name": self.friendly_name or self.name,
                    "api_version": "1.5.0",  # Added from BasicEntity
                    "manufacturer": self.manufacturer,
                    "model": self.model,
                    "name": self.name,
                    "project_name": self.project_name,
                },
                server=hostname,
            )

            await zeroconf.async_register_service(service_info)
            self.service_info = service_info
            return zeroconf
        except Exception as e:
            logger.error(f"Error registering zeroconf: {e}", exc_info=True)
            return None

    async def unregister_zeroconf(self):
        if self.zeroconf and self.service_info:
            try:
                await self.zeroconf.async_unregister_service(self.service_info)
                await self.zeroconf.async_close()
            except Exception as e:
                logger.error(f"Error unregistering zeroconf: {e}", exc_info=True)