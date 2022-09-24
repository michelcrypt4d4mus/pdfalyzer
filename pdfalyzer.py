#!/usr/bin/env python
import code
from os import path

# load_dotenv() should be called before parsing local libary
from dotenv import load_dotenv; load_dotenv()

from lib.helpers.rich_text_helper import PDFALYZER_TERMINAL_THEME, console
from lib.pdf_walker import PdfWalker
from lib.util.argument_parser import output_sections, parse_arguments
from lib.util.logging import log


args = parse_arguments()
walker = PdfWalker(args.pdf)

for (arg, method) in output_sections(args, walker):
    if args.output_dir:
        console.record = True
        file_prefix = (args.file_prefix + '_') if args.file_prefix else  ''
        output_file_basename = f"{file_prefix}{path.basename(args.pdf)}.{method.__name__.removeprefix('print_')}."
        output_file = path.join(args.output_dir, f"{output_file_basename}{args.output_file_extension}")
        print(f'Exporting {arg} data to {output_file}...')

    method()

    if args.output_dir:
        if args.export_svgs:
            console.save_svg(output_file, theme=PDFALYZER_TERMINAL_THEME, title=output_file_basename)
        if args.export_html:
            console.save_html(output_file, theme=PDFALYZER_TERMINAL_THEME, inline_styles=True)
        elif args.txt_output_to:
            console.save_text(output_file, styles=True)

        print(f'Exported {arg} data to {output_file}.')


# Drop into interactive shell if requested
if args.interact:
    code.interact(local=locals())
