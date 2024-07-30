from __future__ import annotations

import asyncio
import socket
import logging

from . import (  # type: ignore
    BasicEntity,
    ConnectRequest,
    ConnectResponse,
    DeviceInfoRequest,
    DeviceInfoResponse,
    DisconnectRequest,
    DisconnectResponse,
    GetTimeRequest,
    GetTimeResponse,
    HelloRequest,
    HelloResponse,
    ListEntitiesDoneResponse,
    ListEntitiesRequest,
    MESSAGE_TYPE_TO_PROTO,
    PingRequest,
    PingResponse,
    SubscribeHomeAssistantStatesRequest,
    SubscribeHomeassistantServicesRequest,
    SubscribeLogsRequest,
    SubscribeLogsResponse,
    SubscribeStatesRequest,
)

PROTO_TO_MESSAGE_TYPE = {v: k for k, v in MESSAGE_TYPE_TO_PROTO.items()}

logger = logging.getLogger(__name__)

def _varuint_to_bytes(value: int) -> bytes:
    """Convert a varuint to bytes."""
    if value <= 0x7F:
        return bytes((value,))

    result = bytearray()
    while value:
        temp = value & 0x7F
        value >>= 7
        if value:
            result.append(temp | 0x80)
        else:
            result.append(temp)
    return bytes(result)

class NativeApiConnection:
    def __init__(self, server, reader, writer):
        self.server = server
        self.reader = reader
        self.writer = writer
        self.subscribe_to_logs = False
        self.subscribe_to_states = False
        self.running = True

    async def start(self):
        while self.running:
            try:
                heartbeat_task = asyncio.create_task(self.heartbeat())
                while self.running:
                    await self.handle_next_message()
            except ConnectionResetError:
                logger.warning("Connection reset. Attempting to reconnect...")
                await self.handle_connection_reset()
            except asyncio.CancelledError:
                logger.info("Connection cancelled. Shutting down...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in connection: {e}", exc_info=True)
                await asyncio.sleep(5)  # Wait before retrying
            finally:
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass

    async def heartbeat(self):
        while self.running:
            try:
                await asyncio.wait_for(self.write_message(PingRequest()), timeout=5.0)
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
            except asyncio.TimeoutError:
                logger.warning("Heartbeat timed out, attempting to reconnect...")
                await self.handle_connection_reset()
            except Exception as e:
                logger.error(f"Heartbeat failed: {e}")
                await self.handle_connection_reset()

    async def handle_next_message(self):
        try:
            msg = await self.read_next_message()

            if msg is None:
                return

            await self.server.log(f"{type(msg)}: {msg}")

            if type(msg) == HelloRequest:
                await self.handle_hello(msg)
            elif type(msg) == ConnectRequest:
                await self.handle_connect(msg)
            elif type(msg) == DisconnectRequest:
                await self.handle_disconnect(msg)
            elif type(msg) == SubscribeLogsRequest:
                await self.handle_subscribe_logs(msg)
            elif type(msg) == PingRequest:
                await self.handle_ping(msg)
            elif type(msg) == SubscribeStatesRequest:
                await self.handle_subscribe_states(msg)
            else:
                await self.server.handle_client_request(self, msg)
        except asyncio.IncompleteReadError:
            logger.warning("Incomplete read. Connection might be closed.")
            raise ConnectionResetError

    async def handle_hello(self, msg):
        resp = HelloResponse(api_version_major=1, api_version_minor=10)
        await self.write_message(resp)

    async def handle_connect(self, msg):
        resp = ConnectResponse()
        await self.write_message(resp)

    async def handle_disconnect(self, msg):
        resp = DisconnectResponse()
        await self.write_message(resp)
        await self.stop()

    async def handle_subscribe_logs(self, msg):
        self.subscribe_to_logs = True

        resp = SubscribeLogsResponse()
        resp.level = msg.level
        resp.message = b'Subscribed to logs'

        await self.write_message(resp)

    async def handle_subscribe_states(self, msg):
        self.subscribe_to_states = True
        await self.server.log("Subscribed to states")
        await self.server.send_all_states(self)

    async def handle_ping(self, msg):
        resp = PingResponse()
        await self.write_message(resp)

    async def log(self, message):
        resp = SubscribeLogsResponse()
        resp.message = str.encode(message)

        await self.write_message(resp)

    async def read_next_message(self):
        preamble = await self._read_varuint()
        length = await self._read_varuint()
        message_type = await self._read_varuint()

        klass = MESSAGE_TYPE_TO_PROTO.get(message_type)
        if klass is None:
            return None

        msg = klass()
        msg_bytes = await self.reader.read(length)

        msg.MergeFromString(msg_bytes)

        return msg

    async def write_message(self, msg):
        if msg is None:
            return

        try:
            out: list[bytes] = []
            type_: int = PROTO_TO_MESSAGE_TYPE[type(msg)]
            data = msg.SerializeToString()

            out.append(b"\0")
            out.append(_varuint_to_bytes(len(data)))
            out.append(_varuint_to_bytes(type_))
            out.append(data)

            self.writer.write(b"".join(out))
            await self.writer.drain()
        except ConnectionResetError:
            logger.warning("Connection reset while writing message.")
            raise

    async def _read_varuint(self):
        result = 0
        bitpos = 0
        while not self.reader.at_eof():
            val_byte = await self.reader.read(1)
            if len(val_byte) != 1:
                return -1

            val = val_byte[0]
            result |= (val & 0x7F) << bitpos
            if (val & 0x80) == 0:
                return result
            bitpos += 7
        return -1

    async def handle_connection_reset(self):
        logger.info("Connection reset detected. Closing connection.")
        
        try:
            await self.handle_disconnect(DisconnectRequest())
        except Exception as e:
            logger.error(f"Error during disconnect handling: {e}", exc_info=True)

        try:
            if not self.writer.is_closing():
                self.writer.close()
                await asyncio.wait_for(self.writer.wait_closed(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Timed out waiting for writer to close")
        except Exception as e:
            logger.error(f"Error closing writer: {e}", exc_info=True)

        # The connection will be removed from self._clients in the clean_stale_connections task
        self.running = False

    async def stop(self):
        self.running = False
        self.writer.close()
        await self.writer.wait_closed()

class NativeApiServer(BasicEntity):
    def __init__(self, *args, port=6053, **kwargs):
        super().__init__(*args, **kwargs)
        self.port = port
        self._clients = set()
        self.server = None

    async def run(self):
        self.server = await asyncio.start_server(self.handle_client, '0.0.0.0', self.port)
        clean_task = asyncio.create_task(self.clean_stale_connections())
        try:
            await self.device.log(2, "api", f"starting on port {self.port}!")
            async with self.server:
                await self.server.serve_forever()
        finally:
            clean_task.cancel()

    async def log(self, message):
        for client in self._clients:
            if client.subscribe_to_logs:
                await client.log(message)

    async def handle_client(self, reader, writer):
        connection = NativeApiConnection(self, reader, writer)
        self._clients.add(connection)
        try:
            await connection.start()
        finally:
            self._clients.remove(connection)

    async def handle_client_request(self, client, message):
        if type(message) == SubscribeHomeassistantServicesRequest:
            pass
        elif type(message) == SubscribeHomeAssistantStatesRequest:
            pass
        elif type(message) == ListEntitiesRequest:
            await self.handle_list_entities(client, message)
        elif type(message) == DeviceInfoRequest:
            await self.handle_device_info(client)
        else:
            await self.device.publish(self, 'client_request', message)

    async def handle_list_entities(self, client, message):
        for entity in self.device.entities:
            msg = await entity.build_list_entities_response()
            if msg != None:
                await client.write_message(msg)

        done_msg = ListEntitiesDoneResponse()
        await client.write_message(done_msg)

    async def handle_device_info(self, client):
        msg = await self.device.build_device_info_response()
        await client.write_message(msg)

    async def send_all_states(self, client):
        for entity in self.device.entities:
            msg = await entity.build_state_response()
            if msg == None:
                continue
            await client.write_message(msg)

    async def handle(self, key, message):
        if key == 'state_change':
            for client in self._clients:
                if client.subscribe_to_states:
                    await client.write_message(message)

        if key == 'log':
            msg = SubscribeLogsResponse(
                level = message[0],
                message = str.encode(message[1])
            )

            for client in self._clients:
                if client.subscribe_to_logs:
                    await client.write_message(msg)

    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        for client in list(self._clients):
            await client.stop()
        self._clients.clear()

    async def restart(self):
        await self.stop()
        await self.run()

    async def clean_stale_connections(self):
        while True:
            for client in list(self._clients):
                if client.writer.is_closing():
                    self._clients.remove(client)
            await asyncio.sleep(60)  # Run every minute