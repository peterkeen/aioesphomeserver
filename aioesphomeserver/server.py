from __future__ import annotations

import asyncio
import socket
import logging

from aioesphomeapi.api_pb2 import (  # type: ignore
    ConnectRequest,
    ConnectResponse,
    DisconnectRequest,
    DisconnectResponse,
    GetTimeRequest,
    GetTimeResponse,
    HelloRequest,
    HelloResponse,
    PingRequest,
    PingResponse,
    SubscribeLogsRequest,
    SubscribeLogsResponse,
)

from aioesphomeapi.core import (
    MESSAGE_TYPE_TO_PROTO,
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

class Connection:
    def __init__(self, server, reader, writer):
        self.server = server
        self.reader = reader
        self.writer = writer

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
        elif type(msg) == SubscribeLogsRequest:
            await self.handle_subscribe_logs(msg)
        elif type(msg) == PingRequest:
            await self.handle_ping(msg)
        else:
            await self.server.queue_message(self, msg)

    async def handle_hello(self, msg):
        resp = HelloResponse(api_version_major=1, api_version_minor=10)
        await self.write_message(resp)

    async def handle_connect(self, msg):
        resp = ConnectResponse()
        await self.write_message(resp)

    async def handle_subscribe_logs(self, msg):
        self.subscribe_to_logs = True
        
        resp = SubscribeLogsResponse()
        resp.level = msg.level
        resp.message = b'Subscribed to logs'

        await self.write_message(resp)

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
        print(type(msg), msg)
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

class Server:
    def __init__(self):
        self._clients = set()
        self._entities = []

    def add_entity(entity):
        self._entities.append(entity)

    async def run(self):
        server = await asyncio.start_server(self.handle_client, '0.0.0.0', 6053)
        async with server:
            print("starting!")
            await server.serve_forever()

    async def log(self, message):
        print(message)
        for client in self._clients:
            await client.log(message)

    async def handle_client(self, reader, writer):
        connection = Connection(self, reader, writer)
        self._clients.add(connection)
        task = asyncio.create_task(connection.start())
        task.add_done_callback(self._clients.discard)

    async def handle_message(self, client, message):
        for entity in self._entities:
            if await entity.can_handle(message):
                entity.handle(client, message)

async def run_server():
    server = Server()
    await server.run()

asyncio.run(run_server())
