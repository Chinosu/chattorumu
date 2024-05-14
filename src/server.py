#!/usr/bin/env python3

from collections import defaultdict
import os
import asyncio
from asyncio import StreamReader, StreamWriter, Server
from signal import SIGINT, SIGTERM
import logging
import functools
from typing import Callable, Tuple, DefaultDict
from contextlib import suppress
import re

from bidict import bidict

from config import *
import utils
from packet import PacketType, Packet, encode, decode


class ChattorumuServer:
    def __init__(self) -> None:
        self.__clients: dict[str, StreamWriter] = {}
        self.__server: Server = None
        self.__configure_logging()
        self.__nicks: bidict = bidict()  # nick -> username
        self.__server_commands: DefaultDict[
            str, Tuple[Callable[[str, str], str], str]
        ] = None
        self.__configure_server_commands()

    async def run(self) -> None:
        """Start and run the server"""
        self.__server = await asyncio.start_server(
            self.__client_handler, host=SERVER_HOST, port=PORT
        )

        for signal in (SIGINT, SIGTERM):
            asyncio.get_event_loop().add_signal_handler(
                signal, lambda: asyncio.ensure_future(self.__cleanup_server())
            )

        logging.info(f"server started on {SERVER_HOST}:{PORT}")
        with suppress(asyncio.CancelledError):
            async with self.__server:
                await self.__server.serve_forever()
        logging.info("server stopped")

    def __configure_logging(self) -> None:
        """
        Configure Python's logging module to log to a designated log file.
        Adds custom logging levels to categorise incoming and outgoing server traffic.
        """

        utils.addLoggingLevel("PACKET_IN", logging.DEBUG + 1)
        utils.addLoggingLevel("PACKET_OUT", logging.DEBUG + 2)
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
        )

    def __configure_server_commands(self) -> None:
        """Set up commands used by clients."""

        def help(username: str, args: str) -> str:
            return "Help:\n" + "\n".join(
                [tuple[1] for tuple in self.__server_commands.values()]
            )

        def list(username: str, args: str) -> str:
            return "\n".join(self.__clients.keys())

        def nick(username: str, args: str) -> str:
            nick = args
            if len(nick) == 0:
                return "nick cannot be empty"
            if nick in self.__nicks:
                return "nick is already in use"
            if re.search("^z\\d{7}$", nick):
                return "nick cannot be a zID"

            if username in self.__nicks.inverse:
                del self.__nicks.inverse[username]
            self.__nicks[nick] = username
            return f"your name is now <{nick}>"

        def unnick(username: str, args: str) -> str:
            if username not in self.__nicks.inverse:
                return "you are currently not using a nick"
            del self.__nicks.inverse[username]
            return "you nick has been removed"

        def realname(username: str, args: str) -> str:
            nick = args
            return self.__nicks.get(nick, f'noone is using the nick "{nick}"')

        def default(username: str, args: str) -> str:
            return 'unknown command. type "/help" for help.'

        self.__server_commands = defaultdict(
            lambda: (default, None),
            {
                "/help": (help, "/help: provides help for commands"),
                "/list": (list, "/list: lists players on the server"),
                "/nick": (nick, "/nick <name>: changes your nick to <name>"),
                "/unnick": (unnick, "/unnick: removes your nick"),
                "/realname": (
                    realname,
                    "/realname <name>: returns user using the nick",
                ),
            },
        )

    async def __client_handler(
        self, reader: StreamReader, writer: StreamWriter
    ) -> None:
        """
        Handles each client connection.
        - Acquires the client's username, ensuring it is unique
        - Signal that the user joined
        - Enters a message loop until the server or client stops
        - Signal that the user left
        """

        data = await reader.read(MESSAGE_SIZE)
        if not data:
            return
        type, username = decode(data)
        logging.packet_in((type, username))
        if type != PacketType.JOIN:
            return

        if username in self.__clients:
            packet = PacketType.ERROR, f"Already joined as {username}."
            logging.packet_out(packet)
            writer.write(encode(packet))
            await writer.drain()
            with suppress(BrokenPipeError):
                writer.close()
                await writer.wait_closed()
            return

        self.__clients[username] = writer
        await self.__broadcast((PacketType.PLAIN, f"{username} has joined"))
        try:
            while True:
                data = await reader.read(MESSAGE_SIZE)
                if not data:
                    break

                type, content = decode(data)
                logging.packet_in((username, type, content))

                if type != PacketType.MESSAGE:
                    continue

                if content[0] == "/":
                    command, args, *_ = content.split(maxsplit=1) + [""]
                    await self.__send(
                        username,
                        writer,
                        (
                            PacketType.COMMAND_RESULT,
                            self.__server_commands[command][0](username, args),
                        ),
                    )
                    continue

                await self.__broadcast(
                    (
                        PacketType.PLAIN,
                        f"<{self.__nicks.inverse.get(username, username)}> {content}",
                    )
                )

        except BrokenPipeError:
            del self.__clients[writer]
        with suppress(BrokenPipeError):
            writer.close()
            await writer.wait_closed()
        await self.__broadcast((PacketType.PLAIN, f"{username} has left"))

    async def __broadcast(self, packet: Packet) -> None:
        """
        Attempts to send a packet to every client.
        If the attempt fails, the client is removed.
        """

        logging.packet_out(packet)
        encoded = encode(packet)
        clients_to_delete = []

        for username, writer in self.__clients.items():
            try:
                writer.write(encoded)
                await writer.drain()
            except (BrokenPipeError, ConnectionRefusedError, ConnectionResetError):
                clients_to_delete.append(username)

        for username in clients_to_delete:
            self.__clients.pop(username, None)

    async def __send(self, username: str, writer: StreamWriter, packet: Packet) -> None:
        """
        Attemts to send a packet to one client.
        If the attempt fails, the client is removed
        """

        logging.packet_out((f"to: {username}", *packet))
        try:
            writer.write(encode(packet))
            await writer.drain()
        except (BrokenPipeError, ConnectionRefusedError, ConnectionResetError):
            self.__clients.pop(username, None)

    async def __cleanup_server(self) -> None:
        """Terminates every client connection then stops the server event loop"""

        for client in self.__clients.values():
            client.close()
            await client.wait_closed()
        self.__server.close()


if __name__ == "__main__":
    asyncio.run(ChattorumuServer().run())
