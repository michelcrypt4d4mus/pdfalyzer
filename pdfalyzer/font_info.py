"""
Unify font information spread across a bunch of PdfObjects (Font, FontDescriptor,
and FontFile) into a single class.
"""
from PyPDF2._cmap import build_char_map, prepare_cm
from PyPDF2.generic import IndirectObject, PdfObject
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from pdfalyzer.binary.binary_scanner import BinaryScanner
from pdfalyzer.config import PdfalyzerConfig
from pdfalyzer.helpers.bytes_helper import print_bytes
from pdfalyzer.helpers.rich_text_helper import console, get_type_style, subheading_width
from pdfalyzer.helpers.string_helper import pp
from pdfalyzer.util.adobe_strings import (FONT, FONT_DESCRIPTOR, FONT_FILE, FONT_LENGTHS, RESOURCES, SUBTYPE,
     TO_UNICODE, TYPE, W, WIDTHS)
from pdfalyzer.util.logging import log


CHARMAP_WIDTH = 8
CHARMAP_DISPLAY_COLS = 5
CHARMAP_COLUMN_WIDTH = int(CHARMAP_WIDTH * 2.5)
CHARMAP_TITLE = 'Character Mapping (As Extracted By PyPDF2)'

ATTRIBUTES_TO_SHOW_IN_SUMMARY_TABLE = [
    'sub_type',
    'base_font',
    'flags',
    'bounding_box',
]


class FontInfo:
    @classmethod
    def extract_font_infos(cls, obj_with_resources: PdfObject) -> ['FontInfo']:
        """
        Extract all the fonts from a given /Resources PdfObject node.
        obj_with_resources must have '/Resources' because that's what _cmap module expects
        """
        resources = obj_with_resources[RESOURCES]

        if isinstance(resources, IndirectObject):
            resources = resources.get_object()

        fonts = resources.get(FONT)

        if fonts is None:
            log.info(f'No fonts found in {obj_with_resources}')
            return []

        fonts = fonts.get_object()
        return [cls.build(label, font, obj_with_resources) for label, font in fonts.items()]

    @classmethod
    def build(cls, label: str, font_ref: IndirectObject, obj_with_resources) -> 'FontInfo':
        """Build a FontInfo object from a IndirectObject ref to a /Font"""
        font_obj = font_ref.get_object()
        font_descriptor = None
        font_file = None

        if font_obj.get(TYPE) != FONT:
            raise TypeError(f"{TYPE} of {font_ref} is not {FONT}")

        if FONT_DESCRIPTOR in font_obj:
            font_descriptor = font_obj[FONT_DESCRIPTOR].get_object()
            font_file_keys = [k for k in font_descriptor.keys() if FONT_FILE in k]

            # There's /FontFile, /FontFile2, etc. but whichever it is there should be only one
            if len(font_file_keys) > 1:
                raise RuntimeError(f"Too many /FontFile keys in {font_descriptor}: {font_file_keys}")
            elif len(font_file_keys) == 0:
                log.info(f"No font_file found in {font_descriptor}")
            else:
                font_file = font_descriptor[font_file_keys[0]].get_object()

        return cls(label, font_ref.idnum, font_obj, font_descriptor, font_file, obj_with_resources)

    def __init__(self, label, idnum, font, font_descriptor, font_file, obj_with_resources):
        self.label = label
        self.idnum = idnum
        self.font_file = font_file
        self.descriptor = font_descriptor

        # /Font attributes
        self.font = font
        self.sub_type = font.get(SUBTYPE)
        self.widths = font.get(WIDTHS) or font.get(W)

        if isinstance(self.widths, IndirectObject):
            self.widths = self.widths.get_object()

        self.base_font = font.get('/BaseFont')
        self.first_and_last_char = [font.get('/FirstChar'), font.get('/LastChar')]
        self.display_title = f"{self.idnum}. Font {self.label} "

        if self.sub_type is None:
            log.warning(f"Font type not given for {self.display_title}")
            self.display_title += "(UNKNOWN FONT TYPE)"
        else:
            self.display_title += f"({self.sub_type[1:]})"

        # FontDescriptor attributes
        if font_descriptor is not None:
            self.bounding_box = font_descriptor.get('/FontBBox')
            self.flags = font_descriptor.get('/Flags')
        else:
            self.bounding_box = None
            self.flags = None

        # /FontFile attributes
        if font_file is not None:
            self.lengths = [font_file[k] for k in FONT_LENGTHS if k in font_file]
            self.stream_data = font_file.get_data()
            self.advertised_length = sum(self.lengths)
            self.binary_scanner = BinaryScanner(self.stream_data, self)
            self.prepared_char_map = prepare_cm(font) if TO_UNICODE in font else None
            # TODO: shouldn't we be passing ALL the widths?
            self._char_map = build_char_map(label, self.widths[0], obj_with_resources)

            try:
                self.character_mapping = self._char_map[3]
            except (IndexError, TypeError):
                log.warning(f"Exception trying to get character mapping for {self}")
                self.character_mapping = []
        else:
            self.lengths = None
            self.stream_data = None
            self.advertised_length = None
            self.binary_scanner = None
            self.prepared_char_map = None
            self._char_map = None
            self.character_mapping = None

    def width_stats(self):
        if self.widths is None:
            return {}

        return {
            'min': min(self.widths),
            'max': max(self.widths),
            'count': len(self.widths),
            'unique_count': len(set(self.widths)),
        }

    def print_summary(self):
        """Prints a table of info about the font drawn from the various PDF objects. quote_type of None means all."""
        self.print_header_panel()
        console.print(self._summary_table())
        self.print_character_mapping()
        self.print_prepared_charmap()

        if self.binary_scanner is not None:
            self.binary_scanner.print_stream_preview(title_suffix=f" of /FontFile for {self.display_title}")
            self.binary_scanner.check_for_dangerous_instructions()

            if not PdfalyzerConfig.SUPPRESS_DECODES:
                self.binary_scanner.force_decode_all_quoted_bytes()

            self.binary_scanner.print_decoding_stats_table()

        console.line(2)

    def print_character_mapping(self):
        """Prints the character mapping extracted by PyPDF2._charmap in tidy columns"""
        if self.character_mapping is None or len(self.character_mapping) == 0:
            log.info(f"No character map found in {self}")
            return

        console.print(Panel(f"{CHARMAP_TITLE} for {self.display_title}", style='charmap_title', expand=False))
        charmap_keys = list(self.character_mapping.keys())
        mappings_per_col, remainder = divmod(len(charmap_keys), CHARMAP_DISPLAY_COLS)
        mappings_per_col = mappings_per_col if remainder == 0 else mappings_per_col + 1

        cols_of_keys = [
            charmap_keys[(i * mappings_per_col):((i + 1) * mappings_per_col)]
            for i in range(CHARMAP_DISPLAY_COLS)
        ]

        rows_of_keys = [
            [col[i] for col in cols_of_keys if i < len(col)]
            for i in range(mappings_per_col)
        ]

        rows_of_key_value = [
            [type(self)._format_charmap_entry(k, self.character_mapping[k]) for k in row_of_keys]
            for row_of_keys in rows_of_keys
        ]

        for row in rows_of_key_value:
            row = row + [''] if len(row) < CHARMAP_DISPLAY_COLS else row  # Pad the shorthanded column(s)
            format_str = ' '.join([f'{{{i}: >{{width}}}}' for i in range(len(row))])
            console.print(format_str.format(*row, width=CHARMAP_COLUMN_WIDTH))

    def print_prepared_charmap(self):
        """Prints the prepared_charmap returned by PyPDF2"""
        if self.prepared_char_map is None:
            log.info(f"No prepared_charmap found in {self}")
            return

        section_title = f"Adobe PostScript charmap prepared by PyPDF2 for {self.display_title}"
        console.print(Panel(section_title, style='prepared_charmap_title', expand=False))
        print_bytes(self.prepared_char_map, style='prepared_charmap')
        console.print('')

    def preview_bytes_at_advertised_lengths(self):
        """Show the bytes at the boundaries provided by /Length1, /Length2, and /Length3, if they exist"""
        byte_addresses = [0]

        for i in f.lengths[0:2]:
            print(f"{f.descriptor} at length {i}:")
            print(f"\n  Stream before: {f.stream_data[i-200:i+1]}")
            print(f"\n  Stream after: {f.stream_data[i:i+200]}")

        print(f"\nfinal bytes back from {f.lengths[2]} + 10: {f.stream_data[-10 - -f.lengths[2]:]}")

    def print_header_panel(self):
        console.print(Panel(self.display_title, width=subheading_width(), padding=(1, 1)), style='font_title')

    def _summary_table(self):
        """Build a Rich Table with important info about the font"""
        table = Table('', '', show_header=False)
        table.columns[0].style = 'font_property'
        table.columns[0].justify = 'right'

        def add_table_row(name, value):
            table.add_row(name, Text(str(value), get_type_style(type(value))))

        for attr in ATTRIBUTES_TO_SHOW_IN_SUMMARY_TABLE:
            attr_value = getattr(self, attr)
            add_table_row(attr, attr_value)

        add_table_row('/Length properties', self.lengths)
        add_table_row('total advertised length', self.advertised_length)

        if self.binary_scanner is not None:
            add_table_row('actual length', self.binary_scanner.stream_length)

        if self.prepared_char_map is not None:
            add_table_row('prepared charmap length', len(self.prepared_char_map))

        if self._char_map is not None:
            add_table_row('character mapping count', len(self.character_mapping))

        if self.widths is not None:
            for k, v in self.width_stats().items():
                add_table_row(f"char width {k}", v)

        if self.widths is not None:
            if len(set(self.widths)) == 1:
                table.add_row(
                    'char widths',
                    Text(f"{self.widths[0]} (single value repeated {len(self.widths)} times)", style=get_type_style(list)))
            else:
                add_table_row('char widths', self.widths)
                add_table_row('char widths(sorted)', sorted(self.widths))

        col_0_width = max([len(entry) for entry in table.columns[0]._cells]) + 4
        table.columns[1].max_width = subheading_width() - col_0_width - 3
        return table

    def __str__(self):
        return self.display_title

    @staticmethod
    def _format_charmap_entry(k, v):
        return '{0: >{width}} => {1: <{width}}'.format(
            pp.pformat(k),
            pp.pformat(v),
            width=CHARMAP_WIDTH)
