"""
Methods to help with the formatting of the output tables, headers, panels, etc.
"""
from typing import List

from rich import box
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from yaralyzer.output.rich_console import console, console_width

DEFAULT_SUBTABLE_COL_STYLES = ['white', 'bright_white']
HEADER_PADDING = (1, 1)


def generate_subtable(cols: List[str], header_style: str = 'subtable') -> Table:
    """Suited for placement in larger tables."""
    table = Table(
        box=box.SIMPLE,
        show_edge=False,
        collapse_padding=True,
        padding=(0, 0, 0, 0),
        header_style=header_style,
        show_lines=False,
        border_style='grey.dark',
        expand=True)

    for i, col in enumerate(cols):
        if i == 0:
            table.add_column(col, style=DEFAULT_SUBTABLE_COL_STYLES[0], justify='left')
        else:
            table.add_column(col, style='bright_white', justify='right')

    return table


def subheading_width() -> int:
    """Return 75% of the console width."""
    return int(console_width() * 0.75)


def half_width() -> int:
    """Return 50% of the console width."""
    return int(console_width() * 0.5)


def pad_header(header: str) -> Padding:
    """Would pad anything, not just headers"""
    return Padding(header, HEADER_PADDING)


def print_section_header(headline: str, style: str = '') -> None:
    """Prints a full-width section header with padding above and below."""
    console.line(2)
    _print_header_panel(headline, f"{style} reverse", True, console_width(), HEADER_PADDING)
    console.line()


def print_section_subheader(headline: str, style: str = '') -> None:
    """Prints a half-width section subheader with padding above."""
    console.line()
    _print_header_panel(headline, style, True, subheading_width(), HEADER_PADDING)


def print_section_sub_subheader(headline: str, style: str = ''):
    """Prints a half-width section sub-subheader with no padding above."""
    console.line()
    _print_header_panel(headline, style, True, half_width())


def print_headline_panel(headline: str, style: str = ''):
    """Prints a full-width headline panel with no padding above or below."""
    _print_header_panel(headline, style, False, console_width())


def print_fatal_error_panel(headline: str):
    """Prints a full-width red blinking panel for fatal errors."""
    print_headline_panel(headline, style='red blink')


def _print_header_panel(headline: str, style: str, expand: bool, width: int, padding: tuple = (0,)) -> None:
    """Helper to print a rich `Panel` with the given style, width, and padding."""
    console.print(Panel(headline, style=style, expand=expand, width=width or subheading_width(), padding=padding))
