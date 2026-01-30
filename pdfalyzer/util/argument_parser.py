"""
Parse command line arguments for `pdfalyze` and construct the `PdfalyzerConfig` object.
"""
from argparse import ArgumentParser

from rich_argparse_plus import RichHelpFormatterPlus
from yaralyzer.util.argument_parser import (debug, epilog, export, parser as yaralyzer_parser,
     rules, tuning, yaras)
from yaralyzer.util.constants import YARALYZER_UPPER

from pdfalyzer.config import PdfalyzerConfig
from pdfalyzer.detection.constants.binary_regexes import QUOTE_PATTERNS
from pdfalyzer.util.constants import PDFALYZE
from pdfalyzer.util.output_section import ALL_STREAMS

RichHelpFormatterPlus.choose_theme('prince')

DESCRIPTION = "Explore PDF's inner data structure with absurdly large and in depth visualizations. " + \
              "Track the control flow of her darker impulses, scan rivers of her binary data for signs " + \
              "of evil sorcery, and generally peer deep into the dark heart of the Portable Document Format. " + \
              "Just make sure you also forgive her - she knows not what she does."

YARALYZER_HELP_SUFFIX = "\nThese options are only relevant when you use the --yara or --streams option."


####################################################
# Adjust Yaralyzer's option parser in a few places #
####################################################

# Add one more top level argument
yaralyzer_parser.add_argument('--password', help='only required for encrypted PDFs')

# Add one more option to the YARA rules section
yaras.add_argument('--no-default-yara-rules',
                     action='store_true',
                     help='if --yara is selected use only custom rules from --yara-file arg and not the default included YARA rules')

# Add one more option to the Debug section
debug.add_argument('--allow-missed-nodes',
                    action='store_true',
                    help='force pdfalyze to return 0 to shell even if missing nodes encountered')

# Add one more option to yaralyzer's export options
export.add_argument('-bin', '--extract-binary-streams',
                     action='store_const',
                     const='bin',
                     help='extract all binary streams in the PDF to separate files (requires pdf-parser.py)')

# Make sure --extract-binary-streams is grouped with other export options  # TODO: this really sucks.
num_args = len(yaralyzer_parser._actions)
output_dir_idx = [i for i, arg in enumerate(yaralyzer_parser._actions) if '--output-dir' in arg.option_strings][0]

yaralyzer_parser._actions = yaralyzer_parser._actions[:output_dir_idx] + \
                            [yaralyzer_parser._actions[-1]] + \
                            yaralyzer_parser._actions[output_dir_idx:-1]

assert len(yaralyzer_parser._actions) == num_args, "Number of args changed after reorder!"

# Make yara options unrequired (yaralyzer requires one of them)
rules.required = False

for action_group in yaralyzer_parser._action_groups:
    action_group._actions = yaralyzer_parser._actions

# Rename the tuning section, append info about how these are Yaralyzer options
tuning.title = f"{YARALYZER_UPPER} FINE TUNING"
tuning.description = f"{tuning.description}{YARALYZER_HELP_SUFFIX}"
rules.description = f"{rules.description}{YARALYZER_HELP_SUFFIX}"


###############################
# Pdfalyzer's argument parser #
###############################

parser = ArgumentParser(
    formatter_class=RichHelpFormatterPlus,
    description=DESCRIPTION,
    epilog=epilog(PdfalyzerConfig).rstrip(),
    parents=[yaralyzer_parser],  # NOTE: we're extending yaralyzer's parser
    add_help=False
)


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
is_pdfalyze_script = parser.prog.startswith(PDFALYZE)  # startswith() bc on Windows we end up with 'pdfalyze.cmd'?
