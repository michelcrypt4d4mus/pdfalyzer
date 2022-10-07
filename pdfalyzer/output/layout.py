"""
Methods to help with the design of the output
"""
from rich.panel import Panel

from yaralyzer.output.rich_console import console, console_width

HEADER_PADDING = (1, 1)


def subheading_width() -> int:
    return int(console_width() * 0.75)


def half_width() -> int:
    return int(console_width() * 0.5)


def print_section_header(headline: str, style: str = '') -> None:
    console.line(2)
    _print_header_panel(headline, f"{style} reverse", True, console_width(), HEADER_PADDING)
    console.line()


def print_section_subheader(headline: str, style: str = '') -> None:
    console.line()
    _print_header_panel(headline, style, True, subheading_width(), HEADER_PADDING)


def print_section_sub_subheader(headline: str, style: str = ''):
    console.line()
    _print_header_panel(headline, style, True, half_width())


def print_headline_panel(headline, style: str = ''):
    _print_header_panel(headline, style, False, console_width())


def _print_header_panel(headline: str, style: str, expand: bool, width: int, padding: tuple = (0,)) -> None:
    console.print(Panel(headline, style=style, expand=expand, width=width or subheading_width(), padding=padding))
