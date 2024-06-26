import asyncio
from getpass import getuser


from textual import work
from textual.color import Color
from textual.app import App, ComposeResult
from textual.widgets import Input, ListView, ListItem, Label

from config import *
from screens.error import ErrorScreen
from packet import PacketType, encode, decode


class ChattorumuApp(App):
    DEFAULT_CSS = """
    Screen {
        background: $panel
    }
    Input {
        dock: bottom;
        margin: 1 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Input(placeholder="")
        yield ListView(
            ListItem(Label("Chattorumu ^-^")),
            disabled=False,
            initial_index=0,
        )

    async def on_mount(self) -> None:
        """Called when app starts."""
        # self.username = str(random.randrange(10000))
        self.username = getuser()
        self.input = self.query_one(Input)
        self.results = self.query_one(ListView)
        self.input.focus()

        try:
            await self.connect_to_server()
        except (ConnectionRefusedError, asyncio.TimeoutError, OSError):
            self.push_screen(ErrorScreen("Could not connect to server."))
            return

        self.read_messages()

    async def connect_to_server(self) -> None:
        self.reader, self.writer = await asyncio.wait_for(
            asyncio.open_connection(CLIENT_HOST, PORT), timeout=0.5
        )

        self.writer.write(encode((PacketType.JOIN, self.username)))
        await self.writer.drain()

    async def on_input_submitted(self, message: Input.Changed) -> None:
        """A coroutine to handle a text submitted message."""
        self.input.clear()
        if message.value and not str.isspace(message.value):
            self.send_message(message.value)

    @work
    async def read_messages(self) -> None:
        """Infinite loop awaiting for messages from the server"""
        while True:
            data = await self.reader.read(MESSAGE_SIZE)
            if not data:
                self.push_screen(ErrorScreen("Server closed."))
                break

            type, content = decode(data)

            if type == PacketType.ERROR:
                self.push_screen(ErrorScreen(content))
                break

            label = Label(content)
            if type == PacketType.COMMAND_RESULT:
                label.styles.color = Color(128, 128, 128)  # Grey
            await self.results.append(ListItem(label))
            self.results.scroll_relative(y=content.count("\n") + 1)

    @work
    async def send_message(self, message: str) -> None:
        self.writer.write(encode((PacketType.MESSAGE, message.strip())))
        await self.writer.drain()


if __name__ == "__main__":
    ChattorumuApp().run()
