import code
import sys
from datetime import datetime
from os import environ, getcwd, path
from pathlib import Path

from dotenv import load_dotenv
from pypdf import PdfWriter
from pypdf.errors import PdfReadError

# Should be first local import before load_dotenv() (or at least I think it needs to come first)
from pdfalyzer.config import PdfalyzerConfig

# load_dotenv() should be called as soon as possible (before parsing local classes) but not for pytest
if not environ.get('INVOKED_BY_PYTEST', False):
    for dotenv_file in [path.join(dir, '.pdfalyzer') for dir in [getcwd(), path.expanduser('~')]]:
        if path.exists(dotenv_file):
            load_dotenv(dotenv_path=dotenv_file)
            break

from rich.columns import Columns
from rich.panel import Panel
from rich.text import Text
from yaralyzer.helpers.rich_text_helper import prefix_with_plain_text_obj
from yaralyzer.output.file_export import invoke_rich_export
from yaralyzer.output.rich_console import console
from yaralyzer.util.logging import log, log_and_print

from pdfalyzer.helpers.filesystem_helper import file_size_in_mb, set_max_open_files
from pdfalyzer.helpers.rich_text_helper import print_highlighted
from pdfalyzer.output.json_exporter import JsonExporter
from pdfalyzer.output.pdfalyzer_presenter import PdfalyzerPresenter
from pdfalyzer.output.styles.rich_theme import PDFALYZER_THEME_DICT
from pdfalyzer.pdfalyzer import Pdfalyzer
from pdfalyzer.util.argument_parser import (MAX_QUALITY, ask_to_proceed, output_sections, parse_arguments,
     parse_combine_pdfs_args)
from pdfalyzer.util.pdf_parser_manager import PdfParserManager

# For the table shown by running pdfalyzer_show_color_theme
MAX_THEME_COL_SIZE = 35


def pdfalyze():
    args = parse_arguments()
    pdfalyzer = Pdfalyzer(args.file_to_scan_path)
    presenter = PdfalyzerPresenter(pdfalyzer)
    output_basepath = None
    
    # Initialize JSON exporter if needed
    json_exporter = JsonExporter(pdfalyzer) if args.json else None
    json_export_data = {} if args.json else None

    # Binary stream extraction is a special case
    if args.extract_binary_streams:
        log_and_print(f"Extracting binary streams in '{args.file_to_scan_path}' to files in '{args.output_dir}'...")
        PdfParserManager(args.file_to_scan_path).extract_all_streams(args.output_dir)
        log_and_print(f"Binary stream extraction complete, files written to '{args.output_dir}'.\nExiting.\n")
        sys.exit()

    # The method that gets called is related to the argument name. See 'possible_output_sections' list in argument_parser.py
    # Analysis exports wrap themselves around the methods that actually generate the analyses
    for (arg, method) in output_sections(args, presenter):
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
            
        # Handle JSON export
        if args.json and json_exporter:
            json_output_path = None
            if arg == 'docinfo':
                json_output_path = json_exporter.export_document_info(Path(args.output_dir))
            elif arg == 'tree':
                json_output_path = json_exporter.export_tree(Path(args.output_dir))
            elif arg == 'rich':
                # For rich tree, export the detailed tree structure
                json_output_path = json_exporter.export_tree(Path(args.output_dir))
                # Rename file to indicate it's the rich/detailed version
                if json_output_path.exists():
                    rich_path = json_output_path.parent / json_output_path.name.replace('_tree.json', '_rich_tree.json')
                    json_output_path.rename(rich_path)
                    json_output_path = rich_path
            elif arg == 'counts':
                json_output_path = json_exporter.export_summary(Path(args.output_dir))
            elif arg == 'fonts':
                json_output_path = json_exporter.export_fonts(Path(args.output_dir))
            elif arg == 'streams':
                json_output_path = json_exporter.export_streams(Path(args.output_dir))
            elif arg == 'yara':
                # Get YARA matches from the presenter's yaralyzer
                if hasattr(presenter, 'yaralyzer') and hasattr(presenter.yaralyzer, 'yara_matches'):
                    json_output_path = json_exporter.export_yara_results(Path(args.output_dir), presenter.yaralyzer.yara_matches)
            
            if json_output_path:
                json_export_data[arg] = str(json_output_path)
                log_and_print(f"  -> Exported {arg} to JSON: {json_output_path}")

        # Clear the buffer if we have one
        if args.output_dir:
            del console._record_buffer[:]
    
    # If JSON export was requested, create a manifest file
    if args.json and json_export_data:
        manifest_path = Path(args.output_dir) / f"{pdfalyzer.pdf_basename}_manifest.json"
        with open(manifest_path, 'w') as f:
            import json
            json.dump({
                "pdf_file": pdfalyzer.pdf_basename,
                "exports": json_export_data,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        log_and_print(f"\nJSON export complete. Manifest written to: {manifest_path}")

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


def combine_pdfs():
    """
    Utility method to combine multiple PDFs into one. Invocable with 'combine_pdfs PDF1 [PDF2...]'.
    Example: https://github.com/py-pdf/pypdf/blob/main/docs/user/merging-pdfs.md
    """
    args = parse_combine_pdfs_args()
    set_max_open_files(args.number_of_pdfs)
    merger = PdfWriter()

    for pdf in args.pdfs:
        try:
            print_highlighted(f"  -> Merging '{pdf}'...", style='dim')
            merger.append(pdf)
        except PdfReadError as e:
            print_highlighted(f"      -> Failed to merge '{pdf}'! {e}", style='red')
            ask_to_proceed()

    # Iterate through pages and compress, lowering image quality if requested
    # See https://pypdf.readthedocs.io/en/latest/user/file-size.html#reducing-image-quality
    for i, page in enumerate(merger.pages):
        if args.image_quality < MAX_QUALITY:
            for j, img in enumerate(page.images):
                print_highlighted(f"  -> Reducing image #{j + 1} quality on page {i + 1} to {args.image_quality}...", style='dim')
                img.replace(img.image, quality=args.image_quality)

        print_highlighted(f"  -> Compressing page {i + 1}...", style='dim')
        page.compress_content_streams()  # This is CPU intensive!

    print_highlighted(f"\nWriting '{args.output_file}'...", style='cyan')
    merger.compress_identical_objects(remove_identicals=True, remove_orphans=True)
    merger.write(args.output_file)
    merger.close()
    txt = Text('').append(f"  -> Wrote ")
    txt.append(str(file_size_in_mb(args.output_file)), style='cyan').append(" megabytes\n")
    print_highlighted(txt)
