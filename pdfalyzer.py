#!/usr/bin/env python
import code
import sys
from os import environ, path

# load_dotenv() should be called as soon as possible (before parsing local classes)
if not environ.get('INVOKED_BY_PYTEST', False):
    from dotenv import load_dotenv
    load_dotenv()

from lib.helpers.rich_text_helper import console, invoke_rich_export
from lib.pdf_parser_manager import PdfParserManager
from lib.pdf_walker import PdfWalker
from lib.util.argument_parser import output_sections, parse_arguments
from lib.util.logging import log, log_and_print, log_current_config


args = parse_arguments()
log_current_config()
walker = PdfWalker(args.pdf)

# Binary stream extraction is a special case
if args.extract_binary_streams:
    log_and_print(f"Extracting all binary streams in '{args.pdf}' to files in '{args.output_dir}'...")
    PdfParserManager(args.pdf).extract_all_streams(args.output_dir)
    log_and_print(f"Binary stream extraction complete, files written to '{args.output_dir}'.\nExiting.\n")
    sys.exit()


# Analysis exports wrap themselves around the methods that actually generate the analyses
for (arg, method) in output_sections(args, walker):
    if args.output_dir:
        console.record = True
        export_type = method.__name__.removeprefix('print_')
        output_basename = f"{args.output_basename}.{export_type}  (PDFALYZED at {args.invoked_at_str})"
        output_basepath = path.join(args.output_dir, output_basename)
        print(f'Exporting {arg} data to {output_basepath}...')

    method()

    if args.export_txt:
        invoke_rich_export(console.save_text, output_basepath)

    if args.export_html:
        invoke_rich_export(console.save_html, output_basepath)

    if args.export_svg:
        invoke_rich_export(console.save_svg, output_basepath)


# Drop into interactive shell if requested
if args.interact:
    code.interact(local=locals())
