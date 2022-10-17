from numbers import Number

from rich.table import Table
from rich.text import Text
from yaralyzer.helpers.rich_text_helper import CENTER, na_txt, prefix_with_plain_text_obj
from yaralyzer.util.logging import log

from pdfalyzer.helpers.rich_text_helper import pct_txt
from pdfalyzer.output.layout import generate_subtable, half_width, pad_header

# Start rainbow colors here
CHAR_ENCODING_1ST_COLOR_NUMBER = 203
NOT_FOUND_MSG = Text('(not found)', style='grey.dark_italic')


def build_decoding_stats_table(scanner: 'BinaryScanner') -> Table:
    """Diplay aggregate results on the decoding attempts we made on subsets of scanner.bytes"""
    stats_table = _new_decoding_stats_table(scanner.label.plain if scanner.label else '')
    regexes_not_found_in_stream = []

    for pattern, stats in scanner.regex_extraction_stats.items():
        # Set aside the regexes we didn't find so that the ones we did find are at the top of the table
        if stats.match_count == 0:
            regexes_not_found_in_stream.append([str(pattern), NOT_FOUND_MSG, na_txt()])
            continue

        per_encoding_pattern_stats = scanner.regex_extraction_stats[pattern]
        regex_subtable = generate_subtable(cols=['Metric', 'Value'])
        decodes_subtable = generate_subtable(cols=['Encoding', '#', 'Decoded', '#', 'Forced', '#', 'Failed'])

        # Bootstrap regex_table with match_count, bytes_count, easy_decode_count, etc.
        for metric, measure in vars(stats).items():
            if isinstance(measure, Number):
                regex_subtable.add_row(metric, str(measure))

        for i, (encoding, count) in enumerate(stats.was_match_decodable.items()):
            decodes_subtable.add_row(
                Text(encoding, style=f"color({CHAR_ENCODING_1ST_COLOR_NUMBER + 2 * i})"),
                str(count),
                pct_txt(count, stats.match_count),
                str(per_encoding_pattern_stats.was_match_force_decoded[encoding]),
                pct_txt(per_encoding_pattern_stats.was_match_force_decoded[encoding], stats.match_count),
                str(per_encoding_pattern_stats.was_match_undecodable[encoding]),
                pct_txt(per_encoding_pattern_stats.was_match_undecodable[encoding], stats.match_count))

        # Add the outer table row - the one with the encoding name and two subtables
        stats_table.add_row(str(pattern), regex_subtable, decodes_subtable)

    # Append the empty rows for patterns we didn't find in the data
    for row in regexes_not_found_in_stream:
        row[0] = Text(row[0], style='color(235)')
        stats_table.add_row(*row, style='color(232)')

    return stats_table


def _new_decoding_stats_table(title) -> Table:
    """Build an empty table for displaying decoding stats"""
    title = prefix_with_plain_text_obj(title, style='blue underline')
    title.append(": Decoding Attempts Summary Statistics", style='bright_white bold')

    table = Table(
        title=title,
        min_width=half_width(),
        show_lines=True,
        padding=(0, 1),
        style='color(18)',
        border_style='color(111) dim',
        header_style='color(235) on color(249) reverse',
        title_style='color(249) bold')

    def add_column(header, **kwargs):
        table.add_column(pad_header(header.upper()), **kwargs)

    add_column('Byte Pattern', vertical='middle', style='color(25) bold reverse', justify='right')
    add_column('Aggregate Metrics', overflow='fold', justify=CENTER)
    add_column('Per Encoding Metrics', justify=CENTER)
    return table
