import importlib.metadata
import logging
import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from collections import namedtuple
from functools import partial, update_wrapper
from os import environ, getcwd, path
from typing import List

#from rich_argparse import RichHelpFormatter

from pdfalyzer.config import (DEFAULT_MIN_DECODE_LENGTH, DEFAULT_MAX_DECODE_LENGTH,
     SURROUNDING_BYTES_LENGTH_DEFAULT, LOG_DIR_ENV_VAR, PdfalyzerConfig)
from pdfalyzer.detection.constants.binary_regexes import QUOTE_REGEXES
from pdfalyzer.detection.encoding_detector import (CONFIDENCE_SCORE_RANGE, EncodingDetector)
from pdfalyzer.helpers import rich_text_helper
from pdfalyzer.helpers.file_helper import timestamp_for_filename
from pdfalyzer.helpers.rich_text_helper import console, console_width_possibilities
from pdfalyzer.util.logging import invocation_log, log, log_and_print, log_current_config


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


ARGPARSE_LOG_FORMAT = '{0: >30}    {1: <17} {2: <}\n'
ALL_FONTS_OPTION = -1

DESCRIPTION = "Explore PDF's inner data structure with absurdly large and in depth visualizations. " + \
              "Track the control flow of her darker impulses, scan rivers of her binary data for signs " + \
              "of evil sorcery, and generally peer deep into the dark heart of the Portable Document Format. " + \
              "Just make sure you also forgive her - she knows not what she does."

EPILOG = "Values for various config options can be set permanently by a .pdfalyzer file in your home directory; " + \
         "see the documentation for details. " + \
         f"A registry of previous pdfalyzer invocations will be incribed to a file if the '{LOG_DIR_ENV_VAR}' " + \
         "environment variable is configured."


# Positional args, version, help, etc
parser = ArgumentParser(formatter_class=ExplicitDefaultsHelpFormatter, description=DESCRIPTION, epilog=EPILOG)
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
                    const=ALL_FONTS_OPTION,
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

tuning.add_argument('--quote-type',
                    help='scan binary data for quoted data of this type only or all types if not set',
                    choices=list(QUOTE_REGEXES.keys()))

tuning.add_argument('--suppress-chardet', action='store_true',
                    help="suppress the display of the full table of chardet's encoding likelihood scores")

tuning.add_argument('--surrounding-bytes',
                    help="number of bytes to display before and after suspicious strings in font binaries",
                    default=SURROUNDING_BYTES_LENGTH_DEFAULT,
                    metavar='BYTES',
                    type=int)

tuning.add_argument('--suppress-decodes', action='store_true',
                    help='suppress decode attempts for quoted bytes found in font binaries')

tuning.add_argument('--min-decode-length',
                    help='suppress decode attempts for quoted byte sequences shorter than N',
                    default=DEFAULT_MIN_DECODE_LENGTH,
                    metavar='N',
                    type=int)

tuning.add_argument('--max-decode-length',
                    help='suppress decode attempts for quoted byte sequences longer than N',
                    default=DEFAULT_MAX_DECODE_LENGTH,
                    metavar='N',
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
                    help='write files to OUTPUT_DIR instead of current dir, does nothing if not exporting a file')

export.add_argument('-pfx', '--file-prefix',
                    metavar='PREFIX',
                    help='optional string to use as the prefix for exported files of any kind')

export.add_argument('-sfx', '--file-suffix',
                    metavar='SUFFIX',
                    help='optional string to use as the suffix for exported files of any kind')


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
    args = parser.parse_args()

    if args.debug:
        log.setLevel(logging.DEBUG)

    _log_invocation()
    args.invoked_at_str = timestamp_for_filename()

    if args.maximize_width:
        rich_text_helper.console.width = max(console_width_possibilities())

    # Suppressing/limiting output
    PdfalyzerConfig.MIN_DECODE_LENGTH = args.min_decode_length
    PdfalyzerConfig.MAX_DECODE_LENGTH = args.max_decode_length
    PdfalyzerConfig.NUM_SURROUNDING_BYTES = args.surrounding_bytes

    if args.quote_type:
        PdfalyzerConfig.QUOTE_TYPE = args.quote_type

    if args.suppress_decodes:
        PdfalyzerConfig.SUPPRESS_DECODES = args.suppress_decodes

    # chardet.detect() action thresholds
    if args.force_decode_threshold:
        EncodingDetector.force_decode_threshold = args.force_decode_threshold

    if args.force_display_threshold:
        EncodingDetector.force_display_threshold = args.force_display_threshold

    if args.suppress_chardet:
        PdfalyzerConfig.SUPPRESS_CHARDET_OUTPUT = True

    # File export options
    if args.export_svg or args.export_txt or args.export_html or args.extract_binary_streams:
        args.output_dir = args.output_dir or getcwd()
        file_prefix = (args.file_prefix + '__') if args.file_prefix else ''
        args.file_suffix = ('_' + args.file_suffix) if args.file_suffix else ''
        args.output_basename =  f"{file_prefix}{path.basename(args.pdf)}"
    elif args.output_dir:
        log.warning('--output-dir provided but no export option was chosen')

    _log_argparse_result(args)
    log_current_config()
    return args


def output_sections(args, pdfalyzer) -> List[OutputSection]:
    """
    Determine which of the tree visualizations, font scans, etc were requested.
    If nothing was specified the default is to output all sections.
    """
    # Create a partial for print_font_info() because it's the only one that can take an argument
    # partials have no __name__ so update_wrapper() propagates the 'print_font_info' as this partial's name
    font_id = None if args.font == ALL_FONTS_OPTION else args.font
    font_info = partial(pdfalyzer.print_font_info, font_idnum=font_id)
    update_wrapper(font_info, pdfalyzer.print_font_info)

    # Top to bottom is the default order of output
    possible_output_sections = [
        OutputSection('docinfo', pdfalyzer.print_document_info),
        OutputSection('tree', pdfalyzer.print_tree),
        OutputSection('rich', pdfalyzer.print_rich_table_tree),
        OutputSection('font', font_info),
        OutputSection('counts', pdfalyzer.print_summary),
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
    log_msg = 'argparse results:\n' + ARGPARSE_LOG_FORMAT.format('OPTION', 'TYPE', 'VALUE')

    for arg_var in sorted(args_dict.keys()):
        arg_val = args_dict[arg_var]
        row = ARGPARSE_LOG_FORMAT.format(arg_var, type(arg_val).__name__, str(arg_val))
        log_msg += row

    log_msg += "\n"
    invocation_log.info(log_msg)
