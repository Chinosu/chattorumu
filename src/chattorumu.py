import asyncio
import random

from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Input, ListView, ListItem, Label

from constants import *
from screens.error import error_screen


class ChattorumuApp(App):
    CSS_PATH = "chattorumu.tcss"

    def compose(self) -> ComposeResult:
        yield Input(placeholder="")
        yield ListView(
            ListItem(Label("Chattorumu ^-^")),
            disabled=False,
            initial_index=0,
        )

    async def on_mount(self) -> None:
        """Called when app starts."""
        self.username = str(random.randrange(10000))
        self.input = self.query_one(Input)
        self.results = self.query_one(ListView)

        self.input.focus()

        try:
            self.reader, self.writer = await asyncio.open_unix_connection(SOCKET_PATH)
            self.read_messages()
        except ConnectionRefusedError:
            self.push_screen(error_screen("Could not connect to server."))

    async def on_input_submitted(self, message: Input.Changed) -> None:
        """A coroutine to handle a text submitted message."""
        self.input.clear()
        if message.value and not str.isspace(message.value):
            self.send_message(message.value)

    @work
    async def read_messages(self) -> None:
        """Infinite loop awaiting for messages from the server"""
        while True:
            data = await self.reader.read(MAX_MESSAGE_SIZE)
            if not data:
                break

            await self.results.append(ListItem(Label(data.decode())))
            self.results.scroll_down()

        self.push_screen(error_screen("Server closed."))

    @work
    async def send_message(self, message: str) -> None:
        self.writer.write(f"<{self.username}> {message.strip()}".encode())
        await self.writer.drain()


if __name__ == "__main__":
    ChattorumuApp().run()
