"""
Argument parsers for the command line tools other than `pdfalyze` that are included with The Pdfalyzer.

1. combine_pdfs
2. extract_pdf_pages
3. extract_pdf_text
"""
import logging
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from rich_argparse_plus import RichHelpFormatterPlus
from rich.prompt import Confirm
from rich.text import Text
from yaralyzer.helpers.file_helper import files_in_dir
from yaralyzer.util.logging import log

from pdfalyzer.util.argument_parser import ask_to_proceed, exit_with_error
from pdfalyzer.helpers.filesystem_helper import (do_all_files_exist, extract_page_number, file_exists, is_pdf,
     with_pdf_extension)
from pdfalyzer.helpers.rich_text_helper import print_highlighted
from pdfalyzer.util.page_range import PageRangeArgumentValidator

MAX_QUALITY = 10


##################
#  combine_pdfs  #
##################
combine_pdfs_parser = ArgumentParser(
    description="Combine multiple PDFs into one.",
    epilog="If all PDFs end in a number (e.g. 'xyz_1.pdf', 'xyz_2.pdf', etc. sort the files as if those were" +
           " page numbers prior to merging.",
    formatter_class=RichHelpFormatterPlus)

combine_pdfs_parser.add_argument('pdfs',
                                 help='two or more PDFs to combine',
                                 metavar='PDF_PATH',
                                 nargs='+')

combine_pdfs_parser.add_argument('-iq', '--image-quality',
                                 help='image quality for embedded images (can compress PDF at loss of quality)',
                                 choices=range(1, MAX_QUALITY + 1),
                                 default=MAX_QUALITY,
                                 type=int)

combine_pdfs_parser.add_argument('-o', '--output-file',
                                 help='path to write the combined PDFs to',
                                 required=True)


def parse_combine_pdfs_args() -> Namespace:
    """Parse command line args for combine_pdfs script."""
    args = combine_pdfs_parser.parse_args()
    args.output_file = with_pdf_extension(args.output_file)
    confirm_overwrite_txt = Text("Overwrite '").append(args.output_file, style='cyan').append("'?")
    args.number_of_pdfs = len(args.pdfs)

    if args.number_of_pdfs < 2:
        exit_with_error(f"Need at least 2 PDFs to merge.")
    elif not do_all_files_exist(args.pdfs):
        exit_with_error()
    elif file_exists(args.output_file) and not Confirm.ask(confirm_overwrite_txt):
        exit_with_error()

    if all(is_pdf(pdf) for pdf in args.pdfs):
        if all(extract_page_number(pdf) for pdf in args.pdfs):
            print_highlighted("PDFs appear to have page number suffixes so sorting numerically...")
            args.pdfs.sort(key=lambda pdf: extract_page_number(pdf))
        else:
            print_highlighted("PDFs don't seem to end in page numbers so using provided order...", style='yellow')
    else:
        print_highlighted("WARNING: At least one of the PDF args doesn't end in '.pdf'", style='bright_yellow')
        ask_to_proceed()

    print_highlighted(f"\nMerging {args.number_of_pdfs} individual PDFs into '{args.output_file}'...")
    return args


#####################
# extract_pdf_pages #
#####################
page_range_validator = PageRangeArgumentValidator()

extract_pdf_parser = ArgumentParser(
    formatter_class=RichHelpFormatterPlus,
    description="Extract pages from one PDF into a new PDF.",
)

extract_pdf_parser.add_argument('pdf_file', metavar='PDF_FILE', help='PDF to extract pages from')
extract_pdf_parser.add_argument('--debug', action='store_true', help='turn on debug level logging')

extract_pdf_parser.add_argument('--page-range', '-r',
                                type=page_range_validator,
                                help=page_range_validator.HELP_MSG,
                                required=True)

extract_pdf_parser.add_argument('--destination-dir', '-d',
                                help="directory to write the new PDF to",
                                default=Path.cwd())


def parse_pdf_page_extraction_args() -> Namespace:
    args = extract_pdf_parser.parse_args()

    if not is_pdf(args.pdf_file):
        log.error(f"'{args.pdf_file}' is not a PDF.")
        sys.exit(-1)
    elif not Path(args.destination_dir).exists():
        log.error(f"Destination dir '{args.destination_dir}' does not exist.")
        sys.exit(1)

    _set_log_level(args)
    return args


######################
#  extract_pdf_text  #
######################
extract_text_parser = ArgumentParser(
    formatter_class=RichHelpFormatterPlus,
    description="Extract the text from one or more files or directories.",
    epilog="If any of the FILE_OR_DIRs is a directory all PDF files in that directory will be extracted."
)

extract_text_parser.add_argument('file_or_dir', nargs='+', metavar='FILE_OR_DIR')
extract_text_parser.add_argument('--debug', action='store_true', help='turn on debug level logging')

extract_text_parser.add_argument('--page-range', '-r',
                                 type=page_range_validator,
                                 help=f"[PDFs only] {page_range_validator.HELP_MSG}")

extract_text_parser.add_argument('--print-as-parsed', '-p',
                                 action='store_true',
                                 help='print pages as they are parsed instead of waiting until parsing complete')


def parse_text_extraction_args() -> Namespace:
    args = extract_text_parser.parse_args()
    args.files_to_process = []

    for file_or_dir in args.file_or_dir:
        file_path = Path(file_or_dir)

        if not file_path.exists():
            log.error(f"'{file_path}' is not a valid file or directory.")
            sys.exit(-1)
        elif file_path.is_dir():
            args.files_to_process.extend(files_in_dir(file_path, 'pdf'))
        else:
            args.files_to_process.append(file_path)

    if args.page_range and (len(args.files_to_process) > 1 or not is_pdf(args.files_to_process[0])):
        log.error(f"--page-range can only be specified for a single PDF")
        sys.exit(-1)

    _set_log_level(args)
    return args


def _set_log_level(args: Namespace):
    if args.debug:
        log.setLevel(logging.DEBUG)
