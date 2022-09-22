#!/usr/bin/env python
from argparse import ArgumentDefaultsHelpFormatter, ArgumentError, ArgumentParser
from collections import namedtuple
from functools import partial
from os import environ, path
import code
import importlib.metadata
import logging
import sys

from lib.data_stream_handler import (LIMIT_DECODES_LARGER_THAN_ENV_VAR,
     LIMIT_DECODE_OF_QUOTED_BYTES_LONGER_THAN)
from lib.font_info import SUPPRESS_QUOTED_ENV_VAR
from lib.pdf_parser_manager import PdfParserManager
from lib.pdf_walker import PdfWalker
from lib.util.bytes_helper import SURROUNDING_BYTES_ENV_VAR, SURROUNDING_BYTES_LENGTH_DEFAULT
from lib.util.logging import log
from lib.util.string_utils import console


# Tuple to keep our argument selection orderly
OutputSection = namedtuple('OutputSection', ['argument', 'method'])


class ExplicitDefaultsHelpFormatter(ArgumentDefaultsHelpFormatter):
    def _get_help_string(self, action):
        if action.default in (None, False):
            return action.help
        return super()._get_help_string(action)


# Parse arguments
DESCRIPTION = 'Build and print trees, font binary summaries, and other things describing the logical structure of a PDF.' \
              'If no output sections are specified all sections will be printed to STDOUT in the order they are listed ' \
              'as command line options.'

parser = ArgumentParser(description=DESCRIPTION, formatter_class=ExplicitDefaultsHelpFormatter)
parser.add_argument('--version', action='version', version=f"pdfalyzer {importlib.metadata.version('pdfalyzer')}")
parser.add_argument('pdf', metavar='file_to_analyze.pdf', help='PDF file to process')

# Output sections
parser.add_argument('-d', '--docinfo', action='store_true', help='show embedded document info (author, title, timestamps, etc)')
parser.add_argument('-t', '--tree', action='store_true', help='show condensed tree (one line per object)')
parser.add_argument('-r', '--rich', action='store_true', help='show much more detailed tree (one panel per object, all properties of all objects)')

parser.add_argument('-f', '--font',
                    nargs='?',
                    const=-1,
                    metavar='ID',
                    type=int,
                    help="scan font binaries for 'sus' content, optionally limited to PDF objs w/[ID] (use '--' to avoid positional mixups)")

parser.add_argument('-c', '--counts', action='store_true', help='show counts of some of the properties of the objects in the PDF')

# Fine tuning
parser.add_argument('--suppress-decodes',
                    action='store_true',
                    help='suppress ALL decode attempts for quoted bytes found in font binaries')

parser.add_argument('--limit-decodes',
                    metavar='MAX',
                    type=int,
                    default=LIMIT_DECODE_OF_QUOTED_BYTES_LONGER_THAN,
                    help=f'suppress decode attempts for quoted byte sequences longer than MAX')

parser.add_argument('--surrounding',
                    metavar='BYTES',
                    type=int,
                    default=SURROUNDING_BYTES_LENGTH_DEFAULT,
                    help=f"number of bytes to display before and after suspicious strings in font binaries")

# Export options
parser.add_argument('-txt', '--txt-output-to',
                    metavar='OUTPUT_DIR',
                    help='write analysis to uncolored text files in OUTPUT_DIR (in addition to STDOUT)')

parser.add_argument('-svg', '--export-svgs',
                    metavar='SVG_OUTPUT_DIR',
                    help='export SVG images of the analysis to SVG_OUTPUT_DIR (in addition to STDOUT)')

parser.add_argument('-x', '--extract-streams-to',
                    metavar='STREAM_DUMP_DIR',
                    help='extract all binary streams in the PDF to files in STREAM_DUMP_DIR then exit (requires pdf-parser.py)')

# Debugging
parser.add_argument('-I', '--interact', action='store_true', help='drop into interactive python REPL when parsing is complete')
parser.add_argument('-D', '--debug', action='store_true', help='show extremely verbose debug log output')


# Handle the options
args = parser.parse_args()

if args.extract_streams_to:
    PdfParserManager(args.pdf).extract_all_streams(args.extract_streams_to)
    sys.exit()

if args.txt_output_to and args.export_svgs:
    raise ArgumentError("Can't write to file and export SVG at the same time")

if not args.debug:
    log.setLevel(logging.WARNING)

if args.surrounding and args.surrounding != SURROUNDING_BYTES_LENGTH_DEFAULT:
    environ[SURROUNDING_BYTES_ENV_VAR] = str(args.surrounding)

if args.suppress_decodes:
    environ[SUPPRESS_QUOTED_ENV_VAR] = 'True'

environ[LIMIT_DECODES_LARGER_THAN_ENV_VAR] = str(args.limit_decodes)


# Execute
walker = PdfWalker(args.pdf)

# Top to bottom is the default order of output
OUTPUT_SECTIONS = [
    OutputSection('docinfo', walker.print_document_info),
    OutputSection('tree', walker.print_tree),
    OutputSection('rich', walker.print_rich_table_tree),
    OutputSection('font', partial(walker.print_font_info, font_idnum=None if args.font == -1 else args.font)),
    OutputSection('counts', walker.print_summary),
]

output_sections = [section for section in OUTPUT_SECTIONS if vars(args)[section.argument]]


if len(output_sections) == 0:
    log.info("No section specified; outputting everything...")
    output_sections = OUTPUT_SECTIONS


for (arg, method) in output_sections:
    if args.export_svgs or args.txt_output_to:
        console.record = True
        output_dir = args.export_svgs or args.txt_output_to
        output_file_basename = f"{path.basename(args.pdf)}.{method.__name__.removeprefix('print_')}."

        if args.export_svgs:
            output_file_extension = 'svg'
        elif args.txt_output_to:
            output_file_extension = 'txt'

        output_file = path.join(output_dir, f"{output_file_basename}{output_file_extension}")

    method()

    if args.export_svgs:
        console.save_svg(output_file, title=output_file_basename)
        print(f'Wrote {arg} output SVG data to {output_file}.')
    elif args.txt_output_to:
        console.save_text(output_file)


# Drop into interactive shell if requested
if args.interact:
    code.interact(local=locals())
