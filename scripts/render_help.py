#!/usr/bin/env python
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from os import getcwd, path

from rich.console import Console
from rich.terminal_theme import TerminalTheme
from rich.text import Text
from rich.theme import Theme
from rich_argparse import RichHelpFormatter

from pdfalyzer.util.argument_parser import parser

PROGRAM_NAME = getcwd().split(path.sep)[-1]

TERMINAL_THEME = TerminalTheme(
    (0, 0, 0),
    (255, 255, 255),
    [
        (0, 0, 0),
        (128, 0, 0),
        (0, 128, 0),
        (128, 128, 0),
        (0, 0, 128),
        (128, 0, 128),
        (0, 128, 128),
        (192, 192, 192),
    ],
    [
        (128, 128, 128),
        (255, 0, 0),
        (0, 255, 0),
        (255, 255, 0),
        (0, 0, 255),
        (255, 0, 255),
        (0, 255, 255),
        (255, 255, 255),
    ]
)


def _render_help(program_name: str, export_format: str, output_dir: str) -> str:
    """Render the contents of the help screen to an HTML, SVG, or colored text file"""
    console = Console(record=True, theme=Theme(RichHelpFormatter.styles))
    export_method_name = f"save_{export_format}"
    export_method = getattr(console, export_method_name)
    extension = 'txt' if export_format == 'text' else export_format
    output_file = path.join(output_dir, f"{program_name}_help.{extension}")

    export_kwargs = {
        "save_html": {"theme": TERMINAL_THEME, "inline_styles": True},
        "save_svg": {"theme": TERMINAL_THEME, "title": f"{program_name} --help"},
        "save_text": {"styles": True},
    }

    console.print(Text.from_ansi(parser.format_help()))
    export_method(output_file, **export_kwargs[export_method_name])
    console.print(f"\n\nInvoked Rich.console.{export_method_name}('{output_file}')", style='cyan')
    console.print(f"   * kwargs: '{export_kwargs[export_method_name]}'...\n", style='cyan')
    console.print(f"Rendered help to '{output_file}'", style='cyan')
    return output_file


render_parser = ArgumentParser(
    description='Render the --help.',
    formatter_class=ArgumentDefaultsHelpFormatter)

render_parser.add_argument('--program-name', '-p', help='program the help is for', default=PROGRAM_NAME)
render_parser.add_argument('--output-dir', '-o', help='output dir to save rendered file', default=getcwd())
render_parser.add_argument('--format', '-f', help='render format', choices=['html', 'svg', 'text'], default='svg')
args = render_parser.parse_args()
_render_help(args.program_name, args.format, args.output_dir)
