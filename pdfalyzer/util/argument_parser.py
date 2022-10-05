import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, Action
from collections import namedtuple
from functools import partial, update_wrapper
from importlib.metadata import version
from os import environ, getcwd, path
from typing import List

from rich_argparse import RichHelpFormatter
from yaralyzer.helpers.rich_text_helper import console
from yaralyzer.util.argument_parser import (ExplicitDefaultsHelpFormatter, export, parser,
     parse_arguments as parse_yaralyzer_args)
from yaralyzer.util.logging import log, log_and_print, log_argparse_result, log_current_config, log_invocation

from pdfalyzer.config import LOG_DIR_ENV_VAR, PdfalyzerConfig
from pdfalyzer.detection.constants.binary_regexes import QUOTE_REGEXES

# NamedTuple to keep our argument selection orderly
OutputSection = namedtuple('OutputSection', ['argument', 'method'])

ALL_FONTS_OPTION = -1

DESCRIPTION = "Explore PDF's inner data structure with absurdly large and in depth visualizations. " + \
              "Track the control flow of her darker impulses, scan rivers of her binary data for signs " + \
              "of evil sorcery, and generally peer deep into the dark heart of the Portable Document Format. " + \
              "Just make sure you also forgive her - she knows not what she does."

EPILOG = "Values for various config options can be set permanently by a .pdfalyzer file in your home directory; " + \
         "see the documentation for details. " + \
         f"A registry of previous pdfalyzer invocations will be incribed to a file if the '{LOG_DIR_ENV_VAR}' " + \
         "environment variable is configured."


# Positional args, version, help, etc. Note that we extend the yaralyzer's parser and export
export.add_argument('-bin', '--extract-binary-streams',
                    action='store_const',
                    const='bin',
                    help='extract all binary streams in the PDF to separate files (requires pdf-parser.py)')


parser = ArgumentParser(
    formatter_class=ExplicitDefaultsHelpFormatter,
    description=DESCRIPTION,
    epilog=EPILOG,
    parents=[parser],  # Extend yaralyzer args
    add_help=False)


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
                         "not a multiselect but choosing nothing is still choosing everything. " + \
                         "try '-f -- [the rest]' if you run into an argument position related piccadilly.",
                    nargs='?',
                    const=ALL_FONTS_OPTION,
                    metavar='ID',
                    type=int)

select.add_argument('-y', '--yara', action='store_true',
                    help="scan the PDF and all its decoded/decrypted binary streams with YARA rules")

select.add_argument('--quote-type',
                    help='scan binary data for quoted data of this type only or all types if not set',
                    choices=list(QUOTE_REGEXES.keys()))

# Make sure the selection section is at the top
parser._action_groups = parser._action_groups[:2] + [parser._action_groups[-1]] + parser._action_groups[2:-1]


# The Parsening Begins
def parse_arguments():
    """Parse command line args. Most settings are communicated to the app by setting env vars"""
    if '--version' in sys.argv:
        print(f"pdfalyzer {version('pdfalyzer')}")
        sys.exit()

    args = parser.parse_args()
    args = parse_yaralyzer_args(args)
    log_invocation()

    if args.quote_type:
        PdfalyzerConfig.QUOTE_TYPE = args.quote_type

    # File export options
    if args.export_svg or args.export_txt or args.export_html or args.extract_binary_streams:
        args.output_dir = args.output_dir or getcwd()
        file_prefix = (args.file_prefix + '__') if args.file_prefix else ''
        args.file_suffix = ('_' + args.file_suffix) if args.file_suffix else ''
        args.output_basename =  f"{file_prefix}{path.basename(args.file_to_scan_path)}"
    elif args.output_dir:
        log.warning('--output-dir provided but no export option was chosen')

    log_argparse_result(args)
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
        OutputSection('yara', pdfalyzer.print_yara_results)
    ]

    output_sections = [section for section in possible_output_sections if vars(args)[section.argument]]

    if len(output_sections) == 0:
        log_and_print("No output section specified so outputting all sections...")
        return possible_output_sections
    else:
        return output_sections
