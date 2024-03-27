"""
Methods to help with the design of the output
"""
from rich import box
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from yaralyzer.output.rich_console import console, console_width

DEFAULT_SUBTABLE_COL_STYLES = ['white', 'bright_white']
HEADER_PADDING = (1, 1)


def generate_subtable(cols, header_style='subtable') -> Table:
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
    return int(console_width() * 0.75)


def half_width() -> int:
    return int(console_width() * 0.5)


def pad_header(header: str) -> Padding:
    """Would pad anything, not just headers"""
    return Padding(header, HEADER_PADDING)


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


def print_fatal_error_panel(headline):
    print_headline_panel(headline, style='red blink')


def _print_header_panel(headline: str, style: str, expand: bool, width: int, padding: tuple = (0,)) -> None:
    console.print(Panel(headline, style=style, expand=expand, width=width or subheading_width(), padding=padding))
