"""
Parse command line arguments for pdfalyzer and construct the PdfalyzerConfig object.
"""
import sys
from argparse import ArgumentParser, Namespace
from collections import namedtuple
from functools import partial, update_wrapper
from importlib.metadata import version
from os import getcwd, path
from pathlib import Path
from typing import List, Optional

from rich_argparse_plus import RichHelpFormatterPlus
from rich.prompt import Confirm
from rich.text import Text
from yaralyzer.helpers.file_helper import files_in_dir
from yaralyzer.util.argument_parser import export, parser, parse_arguments as parse_yaralyzer_args, source
from yaralyzer.util.logging import log, log_and_print, log_argparse_result, log_current_config, log_invocation


from pdfalyzer.config import ALL_STREAMS, PDFALYZER, PdfalyzerConfig
from pdfalyzer.detection.constants.binary_regexes import QUOTE_PATTERNS
from pdfalyzer.helpers.filesystem_helper import (do_all_files_exist, extract_page_number, file_exists, is_pdf,
     with_pdf_extension)
from pdfalyzer.helpers.rich_text_helper import print_highlighted
from pdfalyzer.util.page_range import PageRangeArgumentValidator

# NamedTuple to keep our argument selection orderly
OutputSection = namedtuple('OutputSection', ['argument', 'method'])

RichHelpFormatterPlus.choose_theme('prince')

DESCRIPTION = "Explore PDF's inner data structure with absurdly large and in depth visualizations. " + \
              "Track the control flow of her darker impulses, scan rivers of her binary data for signs " + \
              "of evil sorcery, and generally peer deep into the dark heart of the Portable Document Format. " + \
              "Just make sure you also forgive her - she knows not what she does."

EPILOG = "Values for various config options can be set permanently by a .pdfalyzer file in your home directory; " + \
         "see the documentation for details. " + \
         f"A registry of previous pdfalyzer invocations will be inscribed to a file if the " + \
         "{YaralyzerConfig.LOG_DIR_ENV_VAR} environment variable is configured."

# Analysis selection sections
DOCINFO = 'docinfo'
TREE = 'tree'
RICH = 'rich'
FONTS = 'fonts'
COUNTS = 'counts'
YARA = 'yara'
STREAMS = 'streams'
DEFAULT_SECTIONS = [DOCINFO, TREE, RICH, FONTS, COUNTS, YARA]
ALL_SECTIONS = DEFAULT_SECTIONS + [STREAMS]

# Add one more option to yaralyzer's export options
export.add_argument('-bin', '--extract-binary-streams',
                    action='store_const',
                    const='bin',
                    help='extract all binary streams in the PDF to separate files (requires pdf-parser.py)')

# Add one more option to the YARA rules section
source.add_argument('--no-default-yara-rules',
                    action='store_true',
                    help='if --yara is selected use only custom rules from --yara-file arg and not the default included YARA rules')


# Note that we extend the yaralyzer's parser and export
parser = ArgumentParser(
    formatter_class=RichHelpFormatterPlus,
    description=DESCRIPTION,
    epilog=EPILOG,
    parents=[parser],  # Extend yaralyzer args
    add_help=False)


# Output section selection
select = parser.add_argument_group(
    'ANALYSIS SELECTION',
    "Multiselect. Choosing nothing is choosing everything except --streams.")

select.add_argument('-d', '--docinfo', action='store_true',
                    help='show embedded document info (author, title, timestamps, etc.), streams overview, and MD5/SHA hashes')

select.add_argument('-t', '--tree', action='store_true',
                    help='show condensed tree visualization (one line per PDF object)')

select.add_argument('-r', '--rich', action='store_true',
                    help='show much larger / more detailed tree visualization (one row per PDF object property)')

select.add_argument('-f', '--fonts', action='store_true',
                    help="show info about fonts including character mappings for embedded font binaries")

select.add_argument('-y', '--yara', action='store_true',
                    help="scan the PDF with the included malicious PDF YARA rules and/or your custom YARA rules")

select.add_argument('-c', '--counts', action='store_true',
                    help='show counts of some of the properties of the objects in the PDF')

select.add_argument('-s', '--streams',
                    help="scan all the PDF's decoded/decrypted streams for sus content as well as any YARA rule matches. " +
                         "brute force is involved; output is verbose. a single OBJ_ID can be optionally provided to " +
                         "limit the output to a single internal object. try '-s -- [OTHERARGS]' if you run into an " +
                         "argument position related piccadilly.",
                    nargs='?',
                    const=ALL_STREAMS,
                    metavar='ID',
                    type=int)

select.add_argument('--extract-quoted',
                    help="extract and force decode all bytes found between this kind of quotation marks " +
                         "(requires --streams. can be specified more than once)",
                    choices=list(QUOTE_PATTERNS.keys()),
                    dest='extract_quoteds',
                    action='append')

select.add_argument('--suppress-boms', action='store_true',
                    help="don't scan streams for byte order marks (suppresses some of the --streams output)")

select.add_argument('--preview-stream-length',
                    help='number of bytes at the beginning and end of stream data to show as a preview',
                    metavar='BYTES',
                    type=int)

# Make sure the selection section is at the top
parser._action_groups = parser._action_groups[:2] + [parser._action_groups[-1]] + parser._action_groups[2:-1]


################################
# Main argument parsing begins #
################################
def parse_arguments():
    """Parse command line args. Most args can also be communicated to the app by setting env vars."""
    if '--version' in sys.argv:
        print(f"pdfalyzer {version(PDFALYZER)}")
        sys.exit()

    args = parser.parse_args()
    args = parse_yaralyzer_args(args)
    log_invocation()

    if not args.streams:
        if args.extract_quoteds:
            exit_with_error("--extract-quoted does nothing if --streams is not selected")
        if args.suppress_boms:
            log.warning("--suppress-boms has nothing to suppress if --streams is not selected")

    if args.no_default_yara_rules and not args.yara_rules_files:
        exit_with_error("--no-default-yara-rules requires at least one --yara-file argument")

    # File export options
    if args.export_svg or args.export_txt or args.export_html or args.extract_binary_streams:
        args.output_dir = args.output_dir or getcwd()
        file_prefix = (args.file_prefix + '__') if args.file_prefix else ''
        args.file_suffix = ('_' + args.file_suffix) if args.file_suffix else ''
        args.output_basename = f"{file_prefix}{path.basename(args.file_to_scan_path)}"
    elif args.output_dir:
        log.warning('--output-dir provided but no export option was chosen')

    args.extract_quoteds = args.extract_quoteds or []
    PdfalyzerConfig._args = args
    log_argparse_result(args, 'parsed')
    log_current_config()
    return args


def output_sections(args: Namespace, pdfalyzer: 'Pdfalyzer') -> List[OutputSection]:  # noqa: F821
    """
    Determine which of the tree visualizations, font scans, etc should be run.
    If nothing is specified output ALL sections other than --streams which is v. slow/verbose.

    Args:
        args: parsed command line arguments
        pdfalyzer: the `pdfalyzer` instance whose methods will be called to produce output
    Returns:
        List[OutputSection]: List of `OutputSection` namedtuples with 'argument' and 'method' fields
    """
    # Create a partial for print_font_info() because it's the only one that can take an argument
    # partials have no __name__ so update_wrapper() propagates the 'print_font_info' as this partial's name
    stream_id = None if args.streams == ALL_STREAMS else args.streams
    stream_scan = partial(pdfalyzer.print_streams_analysis, idnum=stream_id)
    update_wrapper(stream_scan, pdfalyzer.print_streams_analysis)

    # 1st element string matches the argument in 'select' group
    # 2nd is fxn to call if selected.
    # Top to bottom is the default order of output.
    possible_output_sections = [
        OutputSection(DOCINFO, pdfalyzer.print_document_info),
        OutputSection(TREE, pdfalyzer.print_tree),
        OutputSection(RICH, pdfalyzer.print_rich_table_tree),
        OutputSection(FONTS, pdfalyzer.print_font_info),
        OutputSection(COUNTS, pdfalyzer.print_summary),
        OutputSection(YARA, pdfalyzer.print_yara_results),
        OutputSection(STREAMS, stream_scan),
    ]

    output_sections = [section for section in possible_output_sections if vars(args)[section.argument]]

    if len(output_sections) == 0:
        log_and_print("No output section specified so outputting all sections except --streams...")
        return [section for section in possible_output_sections if section.argument != STREAMS]
    else:
        return output_sections


def all_sections_chosen(args):
    """Returns true if all flags are set or no flags are set."""
    return len([s for s in ALL_SECTIONS if vars(args)[s]]) == len(ALL_SECTIONS)


#############################################################
#  Separate arg parsers for combine_pdfs and other scripts  #
#############################################################

MAX_QUALITY = 10

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


###########################################
# Parse args for extract_pdf_pages() #
###########################################
page_range_validator = PageRangeArgumentValidator()

extract_pdf_parser = ArgumentParser(
    formatter_class=RichHelpFormatterPlus,
    description="Extract pages from one PDF into a new PDF.",
)

extract_pdf_parser.add_argument('pdf_file', metavar='PDF_FILE', help='PDF to extract pages from')

extract_pdf_parser.add_argument('--page-range', '-r',
                                type=page_range_validator,
                                help=page_range_validator.HELP_MSG,
                                required=True)

extract_pdf_parser.add_argument('--destination-dir', '-d',
                                help="directory to write the new PDF to",
                                default=Path.cwd())

extract_pdf_parser.add_argument('--debug', action='store_true', help='turn on debug level logging')


def parse_pdf_page_extraction_args() -> Namespace:
    args = extract_pdf_parser.parse_args()

    if not is_pdf(args.pdf_file):
        log.error(f"'{args.pdf_file}' is not a PDF.")
        sys.exit(-1)
    elif not Path(args.destination_dir).exists():
        log.error(f"Destination dir '{args.destination_dir}' does not exist.")
        sys.exit(1)

    return args


############################################
# Parse args for extract_text_from_pdfs() #
############################################
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
                                 help='print pages as they are parsed instead of waiting until document is fully parsed')


def parse_text_extraction_args() -> Namespace:
    args = extract_text_parser.parse_args()
    args.files_to_process = []

    for file_or_dir in args.file_or_dir:
        file_path = Path(file_or_dir)

        if not file_path.exists():
            log.error(f"File '{file_path}' doesn't exist!")
            sys.exit(-1)
        elif file_path.is_dir():
            args.files_to_process.extend(files_in_dir(file_path, 'pdf'))
        else:
            args.files_to_process.append(file_path)

    if args.page_range and (len(args.files_to_process) > 1 or not is_pdf(args.files_to_process[0])):
        log.error(f"--page-range can only be specified for a single PDF")
        sys.exit(-1)

    return args


#############
#  Helpers  #
#############

def ask_to_proceed() -> None:
    """Exit if user doesn't confirm they want to proceed."""
    if not Confirm.ask(Text("Proceed anyway?")):
        exit_with_error()


def exit_with_error(error_message: Optional[str] = None) -> None:
    """Print 'error_message' and exit with status code 1."""
    if error_message:
        print_highlighted(Text('').append('ERROR', style='bold red').append(f': {error_message}'))

    print_highlighted('Exiting...', style='dim red')
    sys.exit(1)
