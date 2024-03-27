import code
import logging
import sys
from os import environ, getcwd, path

from dotenv import load_dotenv

from pdfalyzer.config import PdfalyzerConfig

# load_dotenv() should be called as soon as possible (before parsing local classes) but not for pytest
if not environ.get('INVOKED_BY_PYTEST', False):
    for dotenv_file in [path.join(dir, '.pdfalyzer') for dir in [getcwd(), path.expanduser('~')]]:
        if path.exists(dotenv_file):
            load_dotenv(dotenv_path=dotenv_file)
            break

from rich.columns import Columns
from rich.panel import Panel
from yaralyzer.helpers.rich_text_helper import prefix_with_plain_text_obj
from yaralyzer.output.file_export import invoke_rich_export
from yaralyzer.output.rich_console import console
from yaralyzer.util.logging import log, log_and_print

from pdfalyzer.output.pdfalyzer_presenter import PdfalyzerPresenter
from pdfalyzer.output.styles.rich_theme import PDFALYZER_THEME_DICT
from pdfalyzer.pdfalyzer import Pdfalyzer
from pdfalyzer.util.pdf_parser_manager import PdfParserManager
from pdfalyzer.util.argument_parser import output_sections, parse_arguments

# For the table shown by running pdfalyzer_show_color_theme
MAX_THEME_COL_SIZE = 35


def pdfalyze():
    args = parse_arguments()
    pdfalyzer = Pdfalyzer(args.file_to_scan_path)
    pdfalyzer = PdfalyzerPresenter(pdfalyzer)
    output_basepath = None

    # Binary stream extraction is a special case
    if args.extract_binary_streams:
        log_and_print(f"Extracting binary streams in '{args.file_to_scan_path}' to files in '{args.output_dir}'...")
        PdfParserManager(args.file_to_scan_path).extract_all_streams(args.output_dir)
        log_and_print(f"Binary stream extraction complete, files written to '{args.output_dir}'.\nExiting.\n")
        sys.exit()

    # Analysis exports wrap themselves around the methods that actually generate the analyses
    for (arg, method) in output_sections(args, pdfalyzer):
        if args.output_dir:
            output_basepath = PdfalyzerConfig.get_output_basepath(method)
            print(f'Exporting {arg} data to {output_basepath}...')
            console.record = True

        method()

        if args.export_txt:
            invoke_rich_export(console.save_text, output_basepath)

        if args.export_html:
            invoke_rich_export(console.save_html, output_basepath)

        if args.export_svg:
            invoke_rich_export(console.save_svg, output_basepath)

        # Clear the buffer if we have one
        if args.output_dir:
            del console._record_buffer[:]

    # Drop into interactive shell if requested
    if args.interact:
        code.interact(local=locals())


def pdfalyzer_show_color_theme() -> None:
    """Utility method to show pdfalyzer's color theme. Invocable with 'pdfalyzer_show_color_theme'."""
    console.print(Panel('The Pdfalyzer Color Theme', style='reverse'))

    colors = [
        prefix_with_plain_text_obj(name[:MAX_THEME_COL_SIZE], style=str(style)).append(' ')
        for name, style in PDFALYZER_THEME_DICT.items()
        if name not in ['reset', 'repr_url']
    ]

    console.print(Columns(colors, column_first=True, padding=(0,3)))
