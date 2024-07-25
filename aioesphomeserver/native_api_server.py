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

def _varuint_to_bytes(value: _int) -> bytes:
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

    async def start(self):
        while True:
            await self.handle_next_message()

    async def handle_next_message(self):
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

    async def handle_hello(self, msg):
        resp = HelloResponse(api_version_major=1, api_version_minor=10)
        await self.write_message(resp)

    async def handle_connect(self, msg):
        resp = ConnectResponse()
        await self.write_message(resp)

    async def handle_disconnect(self, msg):
        resp = DisconnectResponse()
        await self.write_message(resp)
        self.writer.close()
        await self.writer.wait_closed()

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
        if msg == None:
            return

        out: list[bytes] = []
        type_: int = PROTO_TO_MESSAGE_TYPE[type(msg)]
        data = msg.SerializeToString()

        out: list[bytes] = []
        out.append(b"\0")
        out.append(_varuint_to_bytes(len(data)))
        out.append(_varuint_to_bytes(type_))
        out.append(data)

        self.writer.write(b"".join(out))
        await self.writer.drain()

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

class NativeApiServer(BasicEntity):
    def __init__(self, *args, port=6053, **kwargs):
        super().__init__(*args, **kwargs)
        self.port = port
        self._clients = set()

    async def run(self):
        server = await asyncio.start_server(self.handle_client, '0.0.0.0', self.port)
        async with server:
            await self.device.log(2, "api", f"starting on port {self.port}!")
            await server.start_serving()

            while True:
                await asyncio.sleep(3600)

    async def log(self, message):
        for client in self._clients:
            if client.subscribe_to_logs:
                await client.log(message)

    async def handle_client(self, reader, writer):
        connection = NativeApiConnection(self, reader, writer)
        self._clients.add(connection)
        task = asyncio.create_task(connection.start())
        task.add_done_callback(self._clients.discard)

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
                next
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
                    await client.write_message(message)
