from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.containers import Center, Vertical
from textual.widgets import Label, Button


class ErrorScreen(Screen):
    DEFAULT_CSS = """
    Vertical {
        align: center middle;
    }
    Center {
        padding: 1;
    }
    """

    def __init__(
        self,
        error_message: str = "An error occurred.",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name, id, classes)

        self.message = error_message

    def compose(self) -> ComposeResult:
        with Vertical():
            with Center():
                yield Label(self.message)
            with Center():
                yield Button("Okay")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        exit(1)
