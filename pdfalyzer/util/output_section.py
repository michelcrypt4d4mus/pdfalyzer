from argparse import Namespace
from dataclasses import dataclass
from functools import partial, update_wrapper
from typing import Callable, Self

from yaralyzer.util.logging import log

# Analysis selection sections
DOCINFO = 'docinfo'
TREE = 'tree'
RICH = 'rich'
FONTS = 'fonts'
COUNTS = 'counts'
YARA = 'yara'
STREAMS = 'streams'

DEFAULT_SECTIONS = [DOCINFO, TREE, RICH, FONTS, COUNTS, YARA]
ALL_SECTIONS = DEFAULT_SECTIONS + [STREAMS]

ALL_STREAMS = -1


@dataclass
class OutputSection:
    """Helper class to keep track of which analyses are requested by the user."""
    argument: str
    method: Callable

    @classmethod
    def selected_sections(cls, args: Namespace, presenter: 'PdfalyzerPresenter') -> list[Self]:  # noqa: F821
        """
        Determine which of the tree visualizations, font scans, etc should be run.
        If nothing is specified output ALL sections other than --streams which is v. slow/verbose.

        Args:
            args: parsed command line arguments
            pdfalyzer: the `pdfalyzer` instance whose methods will be called to produce output

        Returns:
            list[OutputSection]: List of `OutputSection` namedtuples with 'argument' and 'method' fields
        """
        # Create a partial for print_font_info() because it's the only one that can take an argument
        # partials have no __name__ so update_wrapper() propagates the 'print_font_info' as this partial's name
        stream_id = None if args.streams == ALL_STREAMS else args.streams
        stream_scan = partial(presenter.print_streams_analysis, idnum=stream_id)
        update_wrapper(stream_scan, presenter.print_streams_analysis)

        # 1st element string matches the argument in 'select' group
        # 2nd is fxn to call if selected.
        # Top to bottom is the default order of output.
        possible_output_sections = [
            cls(DOCINFO, presenter.print_document_info),
            cls(TREE, presenter.print_tree),
            cls(RICH, presenter.print_rich_table_tree),
            cls(FONTS, presenter.print_font_info),
            cls(COUNTS, presenter.print_summary),
            cls(YARA, presenter.print_yara_results),
            cls(STREAMS, stream_scan),
        ]

        output_sections = [section for section in possible_output_sections if vars(args)[section.argument]]

        if len(output_sections) == 0:
            log.warning("No output section specified so outputting all sections except --streams...")
            return [section for section in possible_output_sections if section.argument != STREAMS]
        else:
            return output_sections

    @staticmethod
    def all_sections_chosen(args: Namespace) -> bool:
        """Returns True if all flags are set or no flags are set."""
        return len([s for s in ALL_SECTIONS if vars(args)[s]]) == len(ALL_SECTIONS)
