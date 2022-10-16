"""
Table of info about a /Font object hierarchy.
"""
from rich.table import Table
from rich.text import Text

from pdfalyzer.output.layout import subheading_width
from pdfalyzer.output.styles.node_colors import get_class_style

ATTRIBUTES_TO_SHOW_IN_SUMMARY_TABLE = [
    'sub_type',
    'base_font',
    'flags',
    'bounding_box',
]


def font_summary_table(font):
    """Build a Rich Table with important info about the font"""
    table = Table('', '', show_header=False)
    table.columns[0].style = 'font.property'
    table.columns[0].justify = 'right'

    def add_table_row(name, value):
        table.add_row(name, Text(str(value), get_class_style(value)))

    for attr in ATTRIBUTES_TO_SHOW_IN_SUMMARY_TABLE:
        attr_value = getattr(font, attr)
        add_table_row(attr, attr_value)

    add_table_row('/Length properties', font.lengths)
    add_table_row('total advertised length', font.advertised_length)

    if font.binary_scanner is not None:
        add_table_row('actual length', font.binary_scanner.stream_length)
    if font.prepared_char_map is not None:
        add_table_row('prepared charmap length', len(font.prepared_char_map))
    if font._char_map is not None:
        add_table_row('character mapping count', len(font.character_mapping))
    if font.widths is not None:
        for k, v in font.width_stats().items():
            add_table_row(f"char width {k}", v)

        # Check if there's a single number repeated over and over.
        if len(set(font.widths)) == 1:
            table.add_row(
                'char widths',
                Text(
                    f"{font.widths[0]} (single value repeated {len(font.widths)} times)",
                    style=get_class_style(list)
                )
            )
        else:
            add_table_row('char widths', font.widths)
            add_table_row('char widths(sorted)', sorted(font.widths))

    col_0_width = max([len(entry) for entry in table.columns[0]._cells]) + 4
    table.columns[1].max_width = subheading_width() - col_0_width - 3
    return table
