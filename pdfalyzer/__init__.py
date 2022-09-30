import code
import sys
from os import environ, getcwd, path

# load_dotenv() should be called as soon as possible (before parsing local classes) but not for pytest
if not environ.get('INVOKED_BY_PYTEST', False):
    for dotenv_file in [path.join(dir, '.pdfalyzer') for dir in [getcwd(), path.expanduser('~')]]:
        if path.exists(dotenv_file):
            from dotenv import load_dotenv
            print(f"Loading config: {dotenv_file}")
            load_dotenv(dotenv_path=dotenv_file)
            break

from pdfalyzer.config import PdfalyzerConfig
from pdfalyzer.helpers.rich_text_helper import console, invoke_rich_export
from pdfalyzer.util.pdf_parser_manager import PdfParserManager
from pdfalyzer.pdfalyzer import Pdfalyzer
from pdfalyzer.util.argument_parser import ALL_FONTS_OPTION, output_sections, parse_arguments
from pdfalyzer.util.logging import log, log_and_print


def pdfalyze():
    args = parse_arguments()
    walker = Pdfalyzer(args.pdf)

    # Binary stream extraction is a special case
    if args.extract_binary_streams:
        log_and_print(f"Extracting all binary streams in '{args.pdf}' to files in '{args.output_dir}'...")
        PdfParserManager(args.pdf).extract_all_streams(args.output_dir)
        log_and_print(f"Binary stream extraction complete, files written to '{args.output_dir}'.\nExiting.\n")
        sys.exit()


    def get_output_basepath(export_method):
        """Build the path to an output file - everything but the extension"""
        export_type = export_method.__name__.removeprefix('print_')
        output_basename = f"{args.output_basename}.{export_type}"

        if export_type == 'font_info':
            output_basename += '_'

            if args.font != ALL_FONTS_OPTION:
                output_basename += f"_id{args.font}"

            output_basename += f"_maxdecode{PdfalyzerConfig.MAX_DECODE_LENGTH}"

            if args.quote_type:
                output_basename += f"_quote_{args.quote_type}"

        output_basename += args.file_suffix
        return path.join(args.output_dir, output_basename + f"___pdfalyzed_{args.invoked_at_str}")


    # Analysis exports wrap themselves around the methods that actually generate the analyses
    for (arg, method) in output_sections(args, walker):
        if args.output_dir:
            output_basepath = get_output_basepath(method)
            print(f'Exporting {arg} data to {output_basepath}...')
            console.record = True

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
