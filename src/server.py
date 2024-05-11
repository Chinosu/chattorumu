if __name__ != "__main__":
    raise ImportError("This module is not meant to be imported")

import os
import asyncio
from signal import SIGINT, SIGTERM
import logging
import functools

from constants import *


async def handle_client(clients, reader, writer):
    clients.add(writer)

    try:
        while True:
            data = await reader.read(MAX_MESSAGE_SIZE)
            if not data:
                break

            message = data.decode()
            logging.info(f"Received: {message}")

            for client in clients.copy():
                try:
                    client.write(data)
                except (BrokenPipeError, ConnectionResetError) as e:
                    clients.discard(client)
    except BrokenPipeError:
        clients.discard(writer)

    try:
        writer.close()
        await writer.wait_closed()
    except BrokenPipeError:
        pass


async def cleanup(server, clients):
    for client in clients.copy():
        client.close()
        await client.wait_closed()
    server.close()


async def main():
    logging.basicConfig(level=logging.DEBUG)
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    clients = set()

    server = await asyncio.start_unix_server(
        functools.partial(handle_client, clients), path=SOCKET_PATH
    )

    for signal in (SIGINT, SIGTERM):
        asyncio.get_event_loop().add_signal_handler(
            signal, lambda: asyncio.ensure_future(cleanup(server, clients))
        )

    try:
        async with server:
            await server.serve_forever()
    except asyncio.CancelledError:
        pass


asyncio.run(main())
