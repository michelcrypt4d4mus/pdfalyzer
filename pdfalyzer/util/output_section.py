from argparse import Namespace
from dataclasses import dataclass
from functools import partial, update_wrapper
from typing import Callable
from typing import Self

from yaralyzer.util.logging import log_and_print

# Analysis selection sections
DOCINFO = 'docinfo'
TREE = 'tree'
RICH = 'rich'
FONTS = 'fonts'
COUNTS = 'counts'
YARA = 'yara'
STREAMS = 'streams'
ALL_STREAMS = -1


@dataclass
class OutputSection:
    """Helper class to keep track of which analyses are requested by the user."""
    argument: str
    method: Callable

    @classmethod
    def output_sections(cls, args: Namespace, pdfalyzer: 'Pdfalyzer') -> list[Self]:  # noqa: F821
        """
        Determine which of the tree visualizations, font scans, etc should be run.
        If nothing is specified output ALL sections other than --streams which is v. slow/verbose.

        Args:
            args: parsed command line arguments
            pdfalyzer: the `pdfalyzer` instance whose methods will be called to produce output

        Returns:
            List[OutputSection]: List of `OutputSection` namedtuples with 'argument' and 'method' fields
        """
        # Create a partial for print_font_info() because it's the only one that can take an argument
        # partials have no __name__ so update_wrapper() propagates the 'print_font_info' as this partial's name
        stream_id = None if args.streams == ALL_STREAMS else args.streams
        stream_scan = partial(pdfalyzer.print_streams_analysis, idnum=stream_id)
        update_wrapper(stream_scan, pdfalyzer.print_streams_analysis)

        # 1st element string matches the argument in 'select' group
        # 2nd is fxn to call if selected.
        # Top to bottom is the default order of output.
        possible_output_sections = [
            cls(DOCINFO, pdfalyzer.print_document_info),
            cls(TREE, pdfalyzer.print_tree),
            cls(RICH, pdfalyzer.print_rich_table_tree),
            cls(FONTS, pdfalyzer.print_font_info),
            cls(COUNTS, pdfalyzer.print_summary),
            cls(YARA, pdfalyzer.print_yara_results),
            cls(STREAMS, stream_scan),
        ]

        output_sections = [section for section in possible_output_sections if vars(args)[section.argument]]

        if len(output_sections) == 0:
            log_and_print("No output section specified so outputting all sections except --streams...")
            return [section for section in possible_output_sections if section.argument != STREAMS]
        else:
            return output_sections
