"""Helpers for dealing with user interaction."""
import sys

from rich.prompt import Confirm
from rich.text import Text
from yaralyzer.util.logging import log_console


def ask_to_proceed(msg: str | Text | None = None) -> None:
    """Exit if user doesn't confirm they want to proceed."""
    msg = msg if isinstance(msg, Text) else Text(msg or "Proceed anyway?")

    if not Confirm.ask(msg):
        log_console.print('Exiting...', style='dim')
        sys.exit()
