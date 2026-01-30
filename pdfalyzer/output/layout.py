"""
Methods to help with the formatting of the output tables, headers, panels, etc. via Rich.
"""
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from yaralyzer.output.console import console, console_width
from yaralyzer.util.helpers.rich_helper import DEFAULT_TABLE_OPTIONS

from pdfalyzer.util.helpers.rich_helper import indent_padding

HEADER_PADDING = (1, 1)

SUBTABLE_COL_STYLES = [
    {'justify': 'left',  'style': 'white'},
    {'justify': 'right', 'style': 'bright_white'},
]


def generate_subtable(cols: list[str], header_style: str = 'subtable') -> Table:
    """Suited for placement in larger tables."""
    table = Table(
        border_style='grey.dark',
        collapse_padding=True,
        expand=True,
        header_style=header_style,
        padding=(0, 0, 0, 0),
        show_edge=False,
        show_lines=False,
        **DEFAULT_TABLE_OPTIONS,
    )

    for i, col in enumerate(cols):
        table.add_column(col, **SUBTABLE_COL_STYLES[0 if i == 0 else 1])

    return table


def half_width() -> int:
    """Return 50% of the console width."""
    return int(console_width() * 0.5)


def print_fatal_error_panel(headline: str):
    """Prints a full-width red blinking panel for fatal errors."""
    print_headline_panel(headline, style='red blink')


def pad_header(header: str) -> Padding:
    """Would pad anything, not just headers"""
    return Padding(header, HEADER_PADDING)


def print_headline_panel(headline: str, style: str = '', indent: int = 0, internal_padding: tuple | None = None):
    """Prints a full-width headline panel with no padding above or below."""
    _print_header_panel(headline, style, False, console_width(), internal_padding, indent=indent)


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


def subheading_width() -> int:
    """Return 75% of the console width."""
    return int(console_width() * 0.75)


def _print_header_panel(
    headline: str,
    style: str,
    expand: bool,
    width: int,
    internal_padding: tuple | None = None,
    indent: int = 0
) -> None:
    """Helper to print a rich `Panel` with the given style, width, and padding."""
    panel = Panel(
        headline,
        expand=expand,
        padding=internal_padding or (0,),
        style=style,
        width=width or subheading_width(),
        **DEFAULT_TABLE_OPTIONS
    )

    console.print(Padding(panel, indent_padding(indent)))
