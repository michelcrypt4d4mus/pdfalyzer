#!/usr/bin/env python
from argparse import ArgumentError, ArgumentParser
from collections import namedtuple
from os import path
import code
import logging
import sys

from lib.pdf_parser_manager import PdfParserManager
from lib.pdf_walker import PdfWalker
from lib.util.logging import log
from lib.util.string_utils import console

from rich.console import Console


# Tuple to keep our argument selection orderly
OutputSection = namedtuple('OutputSection', ['argument', 'method'])

# Parse arguments
DESCRIPTION = 'Build and print trees, font binary summaries, and other things describing the logical structure of a PDF.' \
              'If no output sections are specified all sections will be printed to STDOUT in the order they are listed ' \
              'as command line options.'

parser = ArgumentParser(description=DESCRIPTION)
parser.add_argument('pdf', metavar='file_to_analyze.pdf', help='PDF file to process')

# Output sections
parser.add_argument('-d', '--docinfo', action='store_true', help='show embedded document info (author, title, timestamps, etc)')
parser.add_argument('-t', '--tree', action='store_true', help='show condensed tree (one line per object)')
parser.add_argument('-r', '--rich', action='store_true', help='show much more detailed tree (one panel per object, all properties of all objects)')
parser.add_argument('-f', '--fonts', action='store_true', help='show info about fonts / scan font binaries for dangerous content)')
parser.add_argument('-c', '--counts', action='store_true', help='show counts of some of the properties of the objects in the PDF')
#parser.add_argument('--no-force-decode', action='store_true', help='skip attempting to force the decoding of binary font data')

# Output options
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
    log.setLevel(logging.ERROR)


# Execute
walker = PdfWalker(args.pdf)

# Top to bottom is the default order of output
OUTPUT_SECTIONS = [
    OutputSection('docinfo', walker.print_document_info),
    OutputSection('tree', walker.print_tree),
    OutputSection('rich', walker.print_rich_table_tree),
    OutputSection('fonts', walker.print_font_info),
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
