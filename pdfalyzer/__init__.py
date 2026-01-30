import code
import sys
from argparse import Namespace

from pypdf import PdfWriter
from pypdf.errors import PdfReadError
from rich.text import Text
from yaralyzer.output.console import console
from yaralyzer.output.file_export import invoke_rich_export
from yaralyzer.util.exceptions import print_fatal_error
from yaralyzer.util.logging import invocation_txt, log_console

from pdfalyzer.config import PdfalyzerConfig
from pdfalyzer.decorators.pdf_file import PdfFile
from pdfalyzer.output.pdfalyzer_presenter import PdfalyzerPresenter
from pdfalyzer.pdfalyzer import Pdfalyzer
from pdfalyzer.util.argument_parser import parser
from pdfalyzer.util.cli_tools.argument_parsers import (MAX_QUALITY, parse_combine_pdfs_args,
     parse_pdf_page_extraction_args, parse_text_extraction_args)
from pdfalyzer.util.exceptions import PdfParserError
from pdfalyzer.util.helpers.filesystem_helper import file_size_in_mb, set_max_open_files
from pdfalyzer.util.helpers.interaction_helper import ask_to_proceed
from pdfalyzer.util.logging import log  # noqa: F401  Trigger log setup
from pdfalyzer.util.output_section import OutputSection
from pdfalyzer.util.pdf_parser_manager import PdfParserManager

PdfalyzerConfig.init(parser)


def pdfalyze():
    """Main entry point for The Pdfalyzer command line tool."""
    args = PdfalyzerConfig.parse_args()

    # Binary stream extraction is a special case
    if args.extract_binary_streams:
        try:
            PdfParserManager.from_args(args).extract_all_streams()
        except PdfParserError as e:
            print_fatal_error('Failed to extract binary streams!', e)

        sys.exit()

    pdfalyzer = Pdfalyzer(args.file_to_scan_path, args.password)
    presenter = PdfalyzerPresenter(pdfalyzer)

    # The method that gets called is related to the argument name. See 'possible_output_sections' list in
    # argument_parser.py. Analysis exports wrap themselves around the methods that actually generate the analyses.
    for section in OutputSection.selected_sections(args, presenter):
        args._export_basepath = PdfalyzerConfig.get_export_basepath(section.method)

        if args.echo_command:
            console.print(invocation_txt())

        section.method()

        if args.export_txt:
            invoke_rich_export(console.save_text, args)
        if args.export_html:
            invoke_rich_export(console.save_html, args)
        if args.export_svg:
            invoke_rich_export(console.save_svg, args)

        # Clear the buffer (if we have one) to make way for next analysis section to be printed into it
        del console._record_buffer[:]

    # Drop into interactive shell if requested
    if args.interact:
        code.interact(local=locals())

    # Non-zero error code if PDF was not verified (must be checked before closing file handle)
    exit_code = int(not bool(pdfalyzer.verifier.was_successful() or args.allow_missed_nodes))
    pdfalyzer.verifier.log_missing_node_warnings()
    pdfalyzer.close()
    exit(exit_code)


def combine_pdfs():
    """
    Script method to combine multiple PDFs into one. Invocable with 'combine_pdfs PDF1 [PDF2...]'.
    Example: https://github.com/py-pdf/pypdf/blob/main/docs/user/merging-pdfs.md
    """
    args = parse_combine_pdfs_args()
    set_max_open_files(args.number_of_pdfs)
    merger = PdfWriter()

    for pdf in args.pdfs:
        try:
            log_console.print(f"  -> Merging '{pdf}'...", style='dim')
            merger.append(pdf)
        except PdfReadError as e:
            log_console.print(f"      -> Failed to merge '{pdf}'! {e}", style='red')
            ask_to_proceed()

    # Iterate through pages and compress, lowering image quality if requested
    # See https://pypdf.readthedocs.io/en/latest/user/file-size.html#reducing-image-quality
    for i, page in enumerate(merger.pages):
        if args.image_quality < MAX_QUALITY:
            for j, img in enumerate(page.images):
                log_console.print(
                    f"  -> Reducing image #{j + 1} quality on page {i + 1} to {args.image_quality}...",
                    style='dim'
                )

                img.replace(img.image, quality=args.image_quality)

        log_console.print(f"  -> Compressing page {i + 1}...", style='dim')
        page.compress_content_streams()  # This is CPU intensive!

    log_console.print(f"\nWriting '{args.output_file}'...")
    merger.compress_identical_objects(remove_identicals=True, remove_orphans=True)
    merger.write(args.output_file)
    merger.close()
    txt = Text('').append(f"  -> Wrote ")
    txt.append(str(file_size_in_mb(args.output_file)), style='cyan').append(" megabytes\n")
    log_console.print(txt)


def extract_pdf_pages() -> None:
    """Extract a range of pages from a PDF to a new PDF."""
    args = parse_pdf_page_extraction_args()
    PdfFile(args.pdf_file).extract_page_range(args.page_range, destination_dir=args.destination_dir)


def extract_pdf_text() -> None:
    """Extract text from a list of file or from all PDF files in a list of directories."""
    args: Namespace = parse_text_extraction_args()
    console.line()

    for file_path in args.files_to_process:
        PdfFile(file_path).print_extracted_text(args.page_range, args.print_as_parsed)
        console.line(2)


def pdfalyzer_install_pdf_parser() -> None:
    PdfParserManager.install_didier_stevens_tools()
