import asyncio
import random

from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Input, ListView, ListItem, Label

from constants import *


class ChattorumuApp(App):
    CSS_PATH = "chattorumu.tcss"

    def compose(self) -> ComposeResult:
        yield Input(placeholder="", id="input")
        yield ListView(
            ListItem(Label("Chattorumu ^-^")),
            disabled=False,
            initial_index=0,
            id="results",
        )

    async def on_mount(self) -> None:
        """Called when app starts."""
        self.username = str(random.randrange(10000))

        self.input = self.query_one(Input)
        self.results = self.query_one(ListView)
        # Give the input focus so we can start typing straight away
        self.input.focus()

        try:
            self.reader, self.writer = await asyncio.open_unix_connection(SOCKET_PATH)
        except ConnectionRefusedError:
            self.exit()

        self.read_messages()

    async def on_input_submitted(self, message: Input.Changed) -> None:
        """A coroutine to handle a text submitted message."""
        if message.value:
            self.input.clear()
            self.send_message(message.value)

    @work
    async def read_messages(self) -> None:
        while True:
            data = await self.reader.read(MAX_MESSAGE_SIZE)
            if not data:
                break
            await self.results.append(ListItem(Label(data.decode())))

    @work
    async def send_message(self, message: str) -> None:
        self.writer.write(f"<{self.username}> {message.strip()}".encode())
        await self.writer.drain()


if __name__ == "__main__":
    ChattorumuApp().run()
