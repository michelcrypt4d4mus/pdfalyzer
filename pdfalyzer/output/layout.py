"""
Methods to help with the design of the output
"""
from rich.panel import Panel

from yaralyzer.output.rich_console import console, console_width



def subheading_width() -> int:
    return int(console_width() * 0.75)


def print_section_header(headline: str, style: str = '') -> None:
    print_section_subheader(headline, f"{style} reverse", True)


def print_section_subheader(headline: str, style: str = '', expand: bool = False) -> None:
    console.line(2)
    console.print(Panel(headline, style=style, expand=expand))
    console.line()
