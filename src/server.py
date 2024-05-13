#!/usr/bin/env python3

import os
import asyncio
from signal import SIGINT, SIGTERM
import logging
import functools
from typing import Tuple

from config import *
import utils
from packet import PacketType, encode, decode


async def handle_client(clients, reader, writer):
    data = await reader.read(MESSAGE_SIZE)
    assert data
    type, username = decode(data)
    logging.incoming((type, username))
    assert type == PacketType.JOIN

    if username in clients:
        packet = PacketType.ERROR, f"Already joined as {username}."
        logging.outgoing(packet)
        writer.write(encode(packet))
        await writer.drain()

        try:
            writer.close()
            await writer.wait_closed()
        except BrokenPipeError:
            pass
        return

    assert username not in clients

    clients[username] = writer
    await broadcast(clients, (PacketType.PLAIN, f"{username} has joined"))

    try:
        while True:
            data = await reader.read(MESSAGE_SIZE)
            if not data:
                break

            type, content = decode(data)
            logging.incoming((username, type, content))

            if type == PacketType.MESSAGE:
                await broadcast(clients, (PacketType.PLAIN, f"<{username}> {content}"))
    except BrokenPipeError:
        del clients[writer]
    try:
        writer.close()
        await writer.wait_closed()
    except BrokenPipeError:
        pass

    await broadcast(clients, (PacketType.PLAIN, f"{username} has left"))


async def broadcast(clients, packet: Tuple[PacketType, str]):
    logging.outgoing(packet)

    clients_to_delete = []
    for username, writer in clients.items():
        try:
            writer.write(encode(packet))
            await writer.drain()
        except (BrokenPipeError, ConnectionResetError):
            clients_to_delete.append(username)

    for username in clients_to_delete:
        clients.pop(username, None)


async def cleanup(server, clients):
    for client in clients.values():
        client.close()
        await client.wait_closed()
    server.close()


async def main():
    utils.addLoggingLevel("INCOMING", logging.DEBUG + 1)
    utils.addLoggingLevel("OUTGOING", logging.DEBUG + 2)
    logging.basicConfig(
        level=logging.OUTGOING,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(LOG_PATH),
            # logging.StreamHandler()
        ],
    )

    if os.path.exists(SOCKET_PATH):
        # Remove old socket
        os.remove(SOCKET_PATH)

    clients = {}

    server = await asyncio.start_unix_server(
        functools.partial(handle_client, clients), path=SOCKET_PATH
    )

    for signal in (SIGINT, SIGTERM):
        asyncio.get_event_loop().add_signal_handler(
            signal, lambda: asyncio.ensure_future(cleanup(server, clients))
        )

    logging.info("server started")

    try:
        async with server:
            await server.serve_forever()
    except asyncio.CancelledError:
        pass

    logging.info("server stopped")


if __name__ == "__main__":
    asyncio.run(main())
