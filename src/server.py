#!/usr/bin/env python3

import os
import asyncio
from signal import SIGINT, SIGTERM
import logging
import functools
from typing import Tuple
from contextlib import suppress

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

        with suppress(BrokenPipeError):
            writer.close()
            await writer.wait_closed()
        return

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

    with suppress(BrokenPipeError):
        writer.close()
        await writer.wait_closed()

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

    clients = {}

    server = await asyncio.start_server(
        functools.partial(handle_client, clients), host=SERVER_HOST, port=PORT
    )

    for signal in (SIGINT, SIGTERM):
        asyncio.get_event_loop().add_signal_handler(
            signal, lambda: asyncio.ensure_future(cleanup(server, clients))
        )

    logging.info(f"server started on {SERVER_HOST}:{PORT}")

    with suppress(asyncio.CancelledError):
        async with server:
            await server.serve_forever()

    logging.info("server stopped")


if __name__ == "__main__":
    asyncio.run(main())
