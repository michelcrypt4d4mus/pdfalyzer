import importlib.metadata
import logging
import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from collections import namedtuple
from functools import partial, update_wrapper
from os import environ, getcwd, path
from typing import List

from rich_argparse import RichHelpFormatter

from lib.config import (DEFAULT_MAX_DECODABLE_CHUNK_SIZE, SURROUNDING_BYTES_LENGTH_DEFAULT,
     PdfalyzerConfig)
from lib.detection.encoding_detector import (CONFIDENCE_SCORE_RANGE, EncodingDetector)
from lib.helpers import rich_text_helper
from lib.helpers.file_helper import timestamp_for_filename
from lib.helpers.rich_text_helper import console, console_width_possibilities
from lib.util.logging import INVOCATION_LOG_PATH, invocation_log, log, log_and_print


# NamedTuple to keep our argument selection orderly
OutputSection = namedtuple('OutputSection', ['argument', 'method'])


# Class to enable defaults to only be printed when they are not None or False
#class ExplicitDefaultsHelpFormatter(RichHelpFormatter):
class ExplicitDefaultsHelpFormatter(ArgumentDefaultsHelpFormatter):
    def _get_help_string(self, action):
        if 'default' in vars(action) and action.default in (None, False):
            return action.help
        else:
            return super()._get_help_string(action)


DESCRIPTION = """Explore PDF's inner data structure with absurdly large and in depth visualizations. Track the control
flow of her darker impulses, scan rivers of her binary data for signs of evil sorcery, and generally peer deep into the
dark heart of the Portable Document Format. Just make sure you also forgive her - she knows not what she does.
"""

EPILOG = f"""
    A registry of previous pdfalyzer invocations will be stored at '{INVOCATION_LOG_PATH}'
    should you need it.
"""

parser = ArgumentParser(
    formatter_class=ExplicitDefaultsHelpFormatter,
    description=DESCRIPTION,
    epilog=EPILOG)

# Positional args, version, help, etc
parser.add_argument('--version', action='version', version=f"pdfalyzer {importlib.metadata.version('pdfalyzer')}")
parser.add_argument('pdf', metavar='file_to_analyze.pdf', help='PDF file to process')


# Output section selection
select = parser.add_argument_group(
    'ANALYSIS SELECTION',
    "Multiselect. Choosing nothing is choosing everything.")

select.add_argument('-d', '--docinfo', action='store_true',
                    help='show embedded document info (author, title, timestamps, etc)')

select.add_argument('-t', '--tree', action='store_true',
                    help='show condensed tree visualization (one line per PDF object)')

select.add_argument('-r', '--rich', action='store_true',
                    help='show much larger / more detailed tree visualization (one row per PDF object property)')

select.add_argument('-c', '--counts', action='store_true',
                    help='show counts of some of the properties of the objects in the PDF')

select.add_argument('-f', '--font',
                    help="scan font binaries for sus content. brute force is involved. brutes are slow and so " + \
                         "is slow. a single font can be optionally be selected by its internal PDF [ID]. " + \
                         "not a multiselect but choosing nothing is still choosing everything. "
                         "try '-f -- [the rest]' if you run into an argument position related piccadilly.",
                    nargs='?',
                    const=-1,
                    metavar='ID',
                    type=int)


# Fine tuning
tuning = parser.add_argument_group(
    'FINE TUNING',
    "Tune various aspects of the analyses and visualizations to your needs. As an example setting " + \
        "a low --max-decode-length (or suppressing brute force binary decode attempts altogether) can " + \
        "dramatically improve run times and only rarely leads to a fatal lack of insight.")

tuning.add_argument('--maximize-width', action='store_true',
                    help="maximize the display width to fill the terminal")

tuning.add_argument('--suppress-chardet', action='store_true',
                    help="suppress the display of the full table of chardet's encoding likelihood scores")

tuning.add_argument('--surrounding-bytes',
                    help="number of bytes to display before and after suspicious strings in font binaries",
                    default=SURROUNDING_BYTES_LENGTH_DEFAULT,
                    metavar='BYTES',
                    type=int)

tuning.add_argument('--suppress-decodes', action='store_true',
                    help='suppress decode attempts for quoted bytes found in font binaries')

tuning.add_argument('--max-decode-length',
                    help='suppress decode attempts for quoted byte sequences longer than MAX',
                    default=DEFAULT_MAX_DECODABLE_CHUNK_SIZE,
                    metavar='MAX',
                    type=int)

tuning.add_argument('--force-display-threshold',
                    help="chardet.detect() scores encodings from 0-100pct but encodings with scores below this number " + \
                         "will not be displayed anywhere",
                    default=EncodingDetector.force_display_threshold,
                    metavar='PCT_CONFIDENCE',
                    type=int,
                    choices=CONFIDENCE_SCORE_RANGE)

tuning.add_argument('--force-decode-threshold',
                    help="extremely high (AKA 'above this number') PCT_CONFIDENCE scores from chardet.detect() " + \
                         "as to the likelihood some binary data was written with a particular encoding will cause " + \
                         "the pdfalyzer to do a force decode of that with that encoding. " + \
                         "(chardet is a sophisticated libary; this is pdfalyzer's way of harnessing that intelligence)",
                    default=EncodingDetector.force_decode_threshold,
                    metavar='PCT_CONFIDENCE',
                    type=int,
                    choices=CONFIDENCE_SCORE_RANGE)


# Export options
export = parser.add_argument_group(
    'FILE EXPORT',
    "Multiselect. Choosing nothing is choosing nothing. Sends what you see on the screen to various file " + \
        "formats in parallel. Writes files to the current directory if --output-dir is not provided. " + \
        "Filenames are expansion of the PDF filename though you can use --file-prefix to make your " +
        "filenames more unique and beautiful to their beholder.")

export.add_argument('-bin', '--extract-binary-streams',
                    action='store_const',
                    const='bin',
                    help='extract all binary streams in the PDF to separate files (requires pdf-parser.py)')

export.add_argument('-svg', '--export-svg',
                    action='store_const',
                    const='svg',
                    help='export analysis to SVG images')

export.add_argument('-txt', '--export-txt',
                    action='store_const',
                    const='txt',
                    help='export analysis to ANSI colored text files')

export.add_argument('-html', '--export-html',
                    action='store_const',
                    const='html',
                    help='export analysis to styled html files')

export.add_argument('-out', '--output-dir',
                    metavar='OUTPUT_DIR',
                    help='write files to OUTPUT_DIR instead of current dir, does nothing if no exporting a file')

export.add_argument('-pfx', '--file-prefix',
                    metavar='PREFIX',
                    help='optional string to use as the prefix for exported files of any kind')


# Debugging
debug = parser.add_argument_group(
    'DEBUG',
    'Debugging/interactive options.')

debug.add_argument('-I', '--interact', action='store_true',
                    help='drop into interactive python REPL when parsing is complete')

debug.add_argument('-D', '--debug', action='store_true',
                    help='show extremely verbose debug log output')


# The Parsening Begins
def parse_arguments():
    """Parse command line args. Most settings are communicated to the app by setting env vars"""
    if not '-h' in sys.argv and not '--help' in sys.argv:
        _log_invocation()

    args = parser.parse_args()
    args.invoked_at_str = timestamp_for_filename()

    if not args.debug:
        log.setLevel(logging.WARNING)

    if args.maximize_width:
        rich_text_helper.console.width = max(console_width_possibilities())

    # Suppressing/limiting output
    PdfalyzerConfig.max_decodable_chunk_size = args.max_decode_length
    PdfalyzerConfig.num_surrounding_bytes = args.surrounding_bytes

    if args.suppress_decodes:
        PdfalyzerConfig.suppress_decodes = args.suppress_decodes

    # chardet.detect() action thresholds
    if args.force_decode_threshold:
        EncodingDetector.force_decode_threshold = args.force_decode_threshold

    if args.force_display_threshold:
        EncodingDetector.force_display_threshold = args.force_display_threshold

    if args.suppress_chardet:
        PdfalyzerConfig.suppress_chardet_output = True

    # File export options
    if args.export_svg or args.export_txt or args.export_html or args.extract_binary_streams:
        args.output_dir = args.output_dir or getcwd()
        file_prefix = (args.file_prefix + '__') if args.file_prefix else  ''
        args.output_basename =  f"{file_prefix}{path.basename(args.pdf)}"
    elif args.output_dir:
        log.warning('--output-dir provided but no export option was chosen')

    _log_argparse_result(args)
    return args


def output_sections(args, pdf_walker) -> List[OutputSection]:
    """
    Determine which of the tree visualizations, font scans, etc were requested.
    If nothing was specified the default is to output all sections.
    """
    # Create a partial for print_font_info() because it's the only one that can take an argument
    # partials have no __name__ so update_wrapper() propagates the 'print_font_info' as this partial's name
    font_info = partial(pdf_walker.print_font_info, font_idnum=None if args.font == -1 else args.font)
    update_wrapper(font_info, pdf_walker.print_font_info)

    # Top to bottom is the default order of output
    possible_output_sections = [
        OutputSection('docinfo', pdf_walker.print_document_info),
        OutputSection('tree', pdf_walker.print_tree),
        OutputSection('rich', pdf_walker.print_rich_table_tree),
        OutputSection('font', font_info),
        OutputSection('counts', pdf_walker.print_summary),
    ]

    output_sections = [section for section in possible_output_sections if vars(args)[section.argument]]

    if len(output_sections) == 0:
        log_and_print("No output section specified so outputting all sections...")
        return possible_output_sections
    else:
        return output_sections


def _log_invocation() -> None:
    """Log the command used to launch the pdfalyzer to the invocation log"""
    invocation_log.info(f"THE INVOCATION: '{' '.join(sys.argv)}'")


def _log_argparse_result(args):
    """Logs the result of argparse"""
    args_dict = vars(args)
    log_msg = ' THE PARSENING:\n'

    for arg_var in sorted(args_dict.keys()):
        arg_val = args_dict[arg_var]
        row = '{0: >30}    {1: ^17} {2: <}\n'.format(arg_var, type(arg_val).__name__, str(arg_val))
        log_msg += row

    invocation_log.info(log_msg + "\n\n\n")
