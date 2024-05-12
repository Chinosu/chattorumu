from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static


class _ErrorScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static(self.message)


def error_screen(message: str):
    err = _ErrorScreen()
    err.message = message
    return err
