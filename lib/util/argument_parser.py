import importlib.metadata
import logging
import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from collections import namedtuple
from functools import partial, update_wrapper
from os import environ

from rich_argparse import RichHelpFormatter

from lib.binary.data_stream_handler import (DEFAULT_MAX_DECODABLE_CHUNK_SIZE,
     MAX_DECODABLE_CHUNK_SIZE_ENV_VAR)
from lib.detection.encoding_detector import (CONFIDENCE_SCORE_RANGE, SUPPRESS_CHARDET_TABLE_ENV_VAR,
     EncodingDetector)
from lib.font_info import SUPPRESS_QUOTED_ENV_VAR
from lib.helpers.bytes_helper import SURROUNDING_BYTES_LENGTH_DEFAULT, SURROUNDING_BYTES_ENV_VAR
from lib.helpers.rich_text_helper import console, console_width_possibilities
from lib.helpers import rich_text_helper
from lib.pdf_parser_manager import PdfParserManager
from lib.util.logging import invocation_log, log


# Class to enable defaults to only be printed when they are not None or False
#class ExplicitDefaultsHelpFormatter(RichHelpFormatter):
class ExplicitDefaultsHelpFormatter(ArgumentDefaultsHelpFormatter):
    def _get_help_string(self, action):
        if 'default' in vars(action) and action.default in (None, False):
            return action.help
        else:
            return super()._get_help_string(action)


# NamedTuple to keep our argument selection orderly
OutputSection = namedtuple('OutputSection', ['argument', 'method'])


DESCRIPTION = "Build and print trees, font binary summaries, and other things describing the logical structure" \
              "of a PDF. If no output sections are specified all sections will be printed to STDOUT in the " \
              "order they are listed as command line options."

parser = ArgumentParser(description=DESCRIPTION, formatter_class=ExplicitDefaultsHelpFormatter)


# Positional args, version, help, etc
parser.add_argument('--version', action='version', version=f"pdfalyzer {importlib.metadata.version('pdfalyzer')}")
parser.add_argument('pdf', metavar='file_to_analyze.pdf', help='PDF file to process')


# Output section selection
select = parser.add_argument_group('OUTPUT SELECTION', 'If none of these chosen pdfalyzer will output them all')

select.add_argument('-d', '--docinfo', action='store_true',
                    help='show embedded document info (author, title, timestamps, etc)')

select.add_argument('-t', '--tree', action='store_true',
                    help='show condensed tree (one line per object)')

select.add_argument('-r', '--rich', action='store_true',
                    help='show much more detailed tree (one panel per object, all properties of all objects)')

select.add_argument('-f', '--font',
                    nargs='?',
                    const=-1,
                    metavar='ID',
                    type=int,
                    help="scan font binaries for 'sus' content, optionally limited to PDF objs w/[ID] " + \
                         "(use '--' to avoid positional mixups)")

select.add_argument('-c', '--counts', action='store_true',
                    help='show counts of some of the properties of the objects in the PDF')


# Fine tuning
tuning = parser.add_argument_group('FINE TUNING', 'Settings that affect aspects of the analyis and output')

tuning.add_argument('--maximize-width', action='store_true',
                    help="maximize the display width to fill the terminal")

tuning.add_argument('--suppress-chardet', action='store_true',
                    help="suppress the display of the full table of chardet's encoding likelihood scores")

tuning.add_argument('--surrounding-bytes',
                    help="number of bytes to display before and after suspicious strings in font binaries",
                    default=SURROUNDING_BYTES_LENGTH_DEFAULT,
                    metavar='BYTES',
                    type=int)

tuning.add_argument('--suppress-decodes',
                    action='store_true',
                    help='suppress decode attempts for quoted bytes found in font binaries')

tuning.add_argument('--max-decode-length',
                    help=f'suppress decode attempts for quoted byte sequences longer than MAX',
                    default=DEFAULT_MAX_DECODABLE_CHUNK_SIZE,
                    metavar='MAX',
                    type=int)

tuning.add_argument('--force-display-threshold',
                    help="chardet.detect() scores encodings from 0-100 pct but only above this are displayed",
                    default=EncodingDetector.force_display_threshold,
                    metavar='PCT_CONFIDENCE',
                    type=int,
                    choices=CONFIDENCE_SCORE_RANGE)

tuning.add_argument('--force-decode-threshold',
                    help="extremely high (AKA 'above this number') PCT_CONFIDENCE scores from chardet.detect() " + \
                         "as to the likelihood some binary data was written with a particular encoding will cause " + \
                         " the pdfalyzer to do a force decode of that with that encoding. " + \
                         "(chardet is a sophisticated libary; this is pdfalyzer's way of harnessing that intelligence)",
                    default=EncodingDetector.force_decode_threshold,
                    metavar='PCT_CONFIDENCE',
                    type=int,
                    choices=CONFIDENCE_SCORE_RANGE)


# Export options
export = parser.add_argument_group('FILE EXPORT', 'Export to various kinds of files')

export.add_argument('-txt', '--txt-output-to',
                    metavar='OUTPUT_DIR',
                    help='write analysis to uncolored text files in OUTPUT_DIR (in addition to STDOUT)')

export.add_argument('-svg', '--export-svgs',
                    metavar='OUTPUT_DIR',
                    help='export SVG images of the analysis to OUTPUT_DIR (in addition to STDOUT)')

export.add_argument('-html', '--export-html',
                    metavar='OUTPUT_DIR',
                    help='export SVG images of the analysis to OUTPUT_DIR (in addition to STDOUT)')

export.add_argument('-str', '--extract-streams-to',
                    metavar='STREAM_DUMP_DIR',
                    help='extract all binary streams in the PDF to files in STREAM_DUMP_DIR then exit (requires pdf-parser.py)')

export.add_argument('-pfx', '--file-prefix',
                    metavar='PREFIX',
                    help='optional string to use as the prefix for exported files of any kind')


# Debugging
debug = parser.add_argument_group('DEBUG', 'Debugging/interactive options')
debug.add_argument('-I', '--interact', action='store_true', help='drop into interactive python REPL when parsing is complete')
debug.add_argument('-D', '--debug', action='store_true', help='show extremely verbose debug log output')



def parse_arguments():
    """Parse command line args. Most settings are communicated to the app by setting env vars"""
    _log_invocation()
    args = parser.parse_args()

    if not args.debug:
        log.setLevel(logging.WARNING)

    # Use pdf-parser to extract binaries then exit
    if args.extract_streams_to:
        console.log("Extracting all the PDF's binary streams to files in STREAM_DUMP_DIR. Will exit on completion.")
        PdfParserManager(args.pdf).extract_all_streams(args.extract_streams_to)
        sys.exit()

    if args.maximize_width:
        #import pdb;pdb.set_trace()
        log.info(f"Console widened to {rich_text_helper.console.width} cols...")
        rich_text_helper.console.width = max(console_width_possibilities())

    # Suppressing/limiting output
    environ[MAX_DECODABLE_CHUNK_SIZE_ENV_VAR] = str(args.max_decode_length)

    if args.surrounding_bytes and args.surrounding_bytes != SURROUNDING_BYTES_LENGTH_DEFAULT:
        environ[SURROUNDING_BYTES_ENV_VAR] = str(args.surrounding_bytes)

    if args.suppress_decodes:
        environ[SUPPRESS_QUOTED_ENV_VAR] = 'True'

    if args.suppress_chardet:
        environ[SUPPRESS_CHARDET_TABLE_ENV_VAR] = 'True'

    # chardet.detect() action thresholds
    if args.force_decode_threshold:
        EncodingDetector.force_decode_threshold = args.force_decode_threshold

    if args.force_display_threshold:
        EncodingDetector.force_display_threshold = args.force_display_threshold


    # File export options
    selected_exports = [arg for arg in [args.txt_output_to, args.export_svgs, args.export_html] if arg]

    if len(selected_exports) > 1:
        raise RuntimeError("Too many exports chosen. Only one export at a time please")
    elif len(selected_exports) == 1:
        if args.export_svgs:
            args.output_file_extension = 'svg'
        elif args.txt_output_to:
            args.output_file_extension = 'txt'
        elif args.export_html:
            args.output_file_extension = 'html'

        args.output_dir = args.export_svgs or args.txt_output_to or args.export_html
    else:
        args.output_dir = None

    _log_argparse_result(args)
    return args


def output_sections(args, pdf_walker) -> [OutputSection]:
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
        log.info("No section specified; outputting everything...")
        return possible_output_sections
    else:
        return output_sections


def _log_invocation() -> None:
    """Log argv to the invocation log"""
    invocation_log.info(f"INVOCATION\n\n    {' '.join(sys.argv)}\n")


def _log_argparse_result(args):
    """Logs the result of argparse"""
    args_dict = vars(args)
    log_msg = 'RESULT OF PARSING THE INVOCATION\n'

    for arg_var in sorted(args_dict.keys()):
        arg_val = args_dict[arg_var]
        row = '{0: >30}    {2: <25} {1: >13}\n'.format(arg_var, type(arg_val).__name__, str(arg_val))
        log_msg += row

    invocation_log.info(log_msg + "\n")
