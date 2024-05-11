if __name__ != "__main__":
    raise ImportError("This module is not meant to be imported")

import asyncio
import logging
import random
import sys
from signal import SIGINT, SIGTERM

from constants import *


# import getpass
# username = getpass.getuser()


async def connect_stdin_stdout():
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)

    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    w_transport, w_protocol = await loop.connect_write_pipe(
        asyncio.streams.FlowControlMixin, sys.stdout
    )
    writer = asyncio.StreamWriter(w_transport, w_protocol, reader, loop)

    return reader, writer


async def handle_server(stdout, reader):
    while True:
        data = await reader.read(MAX_MESSAGE_SIZE)
        if not data:
            break
        stdout.write(f"{data.decode()}\n".encode())
        await stdout.drain()


async def handle_user(stdin, username, writer):
    while True:
        message = await stdin.read(MAX_MESSAGE_SIZE)
        writer.write(f"<{username}> {message.decode().strip()}".encode())
        await writer.drain()


async def main():
    logging.basicConfig(level=logging.DEBUG)
    username = str(random.randrange(1000))
    stdin, stdout = await connect_stdin_stdout()
    try:
        reader, writer = await asyncio.open_unix_connection(SOCKET_PATH)
        writer.write(f"{username} has joined the chat".encode())
        await writer.drain()

        tasks = map(
            asyncio.create_task,
            [handle_server(stdout, reader), handle_user(stdin, username, writer)],
        )

        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        for task in pending:
            task.cancel()
        for task in done:
            task.result()
    except ConnectionRefusedError:
        print("Server unreachable.")

    except asyncio.CancelledError:
        for task in tasks:
            task.cancel()
        writer.write(f"{username} has left the chat".encode())
        await writer.drain()
        writer.close()
        await writer.wait_closed()


asyncio.run(main())
