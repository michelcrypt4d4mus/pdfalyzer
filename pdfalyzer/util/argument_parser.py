"""
Parse command line arguments for `pdfalyze` and construct the `PdfalyzerConfig` object.
"""
import sys
from argparse import ArgumentParser, Namespace
from collections import namedtuple
from importlib.metadata import version
from os import getcwd, path
from typing import Optional

from rich_argparse_plus import RichHelpFormatterPlus
from rich.prompt import Confirm
from rich.text import Text
from yaralyzer.util.argument_parser import debug, export, parser, parse_arguments as parse_yaralyzer_args, source
from yaralyzer.util.logging import log, log_argparse_result, log_current_config, log_invocation

from pdfalyzer.config import PDFALYZE, PDFALYZER, PdfalyzerConfig
from pdfalyzer.detection.constants.binary_regexes import QUOTE_PATTERNS
from pdfalyzer.helpers.rich_text_helper import print_highlighted
from pdfalyzer.util.output_section import ALL_STREAMS, DOCINFO, TREE, RICH, FONTS, COUNTS, STREAMS, YARA

RichHelpFormatterPlus.choose_theme('prince')

DESCRIPTION = "Explore PDF's inner data structure with absurdly large and in depth visualizations. " + \
              "Track the control flow of her darker impulses, scan rivers of her binary data for signs " + \
              "of evil sorcery, and generally peer deep into the dark heart of the Portable Document Format. " + \
              "Just make sure you also forgive her - she knows not what she does."

EPILOG = "Values for various config options can be set permanently by a .pdfalyzer file in your home directory; " + \
         "see the documentation for details. " + \
         f"A registry of previous pdfalyzer invocations will be inscribed to a file if the " + \
         "{YaralyzerConfig.LOG_DIR_ENV_VAR} environment variable is configured."

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

# Add one more option to the Debug section
debug.add_argument('--allow-missed-nodes',
                   action='store_true',
                   help='force pdfalyze to return 0 to shell even if missing nodes encountered')


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
is_pdfalyze_script = (parser.prog == PDFALYZE)


################################
# Main argument parsing begins #
################################
def parse_arguments() -> Namespace:
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


def all_sections_chosen(args: Namespace) -> bool:
    """Returns True if all flags are set or no flags are set."""
    return len([s for s in ALL_SECTIONS if vars(args)[s]]) == len(ALL_SECTIONS)


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
