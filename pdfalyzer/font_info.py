from dataclasses import asdict, dataclass, field, fields
from typing import Self, cast

from pypdf._cmap import prepare_cm
from pypdf._font import Font
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject, NameObject, PdfObject, StreamObject, is_null_or_none
from rich.table import Table
from rich.text import Text
from yaralyzer.output.rich_console import console
from yaralyzer.util.logging import log

from pdfalyzer.binary.binary_scanner import BinaryScanner
from pdfalyzer.helpers.dict_helper import without_nones
from pdfalyzer.output.character_mapping import print_character_mapping, print_prepared_charmap
from pdfalyzer.output.layout import print_section_subheader, subheading_width
from pdfalyzer.output.styles.node_colors import get_class_style, get_label_style
from pdfalyzer.util.adobe_strings import FONT, FONT_FILE, FONT_FILE_KEYS, FONT_LENGTHS, RESOURCES, TO_UNICODE, W, WIDTHS

FONT_SECTION_PREVIEW_LEN = 30
MAX_REPR_STR_LEN = 20

FONT_FLAGS = {
    1: 'monospace',
    2: 'serif',
    3: 'symbolic',
    4: 'script',
    6: 'nonsymbolic',
    7: 'italic',
    17: 'allcaps',
    18: 'smallcaps',
    19: 'forcebold',
}


@dataclass(kw_only=True)
class FontInfo:
    """
    Extract and unify font information.
    """
    label: NameObject | str
    font_indirect: IndirectObject
    font_dict: DictionaryObject = field(init=False)
    font_obj: Font = field(init=False)
    font_file: StreamObject | None = None
    idnum: int = field(init=False)
    lengths: list[int] | None = None
    stream_data: bytes | None = None
    binary_scanner: BinaryScanner | None = None
    prepared_char_map: bytes | None = None
    widths: list[int] | None = None
    # TODO: make methods
    advertised_length: int | None = None
    display_tile: str = ''
    bounding_box: tuple[float, float, float, float] | None = None
    flags: int | None = None
    character_mapping: dict[str, str] | None = None

    def __post_init__(self):
        self.idnum = self.font_indirect.idnum
        self.display_title = f"{self.idnum}. Font {self.label} "

        # /Font attributes
        self.font_dict = cast(DictionaryObject, self.font_indirect.get_object())
        self.font_obj = Font.from_font_resource(self.font_dict)
        self.font_file = self.font_obj.font_descriptor.font_file
        self.widths = self.font_dict.get(WIDTHS) or self.font_dict.get(W)

        if isinstance(self.widths, IndirectObject):
            self.widths = self.widths.get_object()

        if (self.font_obj.sub_type or "Unknown") == "Unknown":
            log.warning(f"Font type not given for {self.display_title}")
            self.display_title += "(UNKNOWN FONT TYPE)"
        else:
            self.display_title += f"({self.font_obj.sub_type})"

        # FontDescriptor attributes
        if not is_null_or_none(self.font_obj.font_descriptor):
            self.bounding_box = self.font_obj.font_descriptor.bbox  # TODO: pypdf has a default value, we want to show real value
            self.flags = int(self.font_obj.font_descriptor.flags)

        self.prepared_char_map = prepare_cm(self.font_dict) if TO_UNICODE in self.font_dict else None
        self.character_mapping = self.font_obj.character_map if self.font_obj.character_map else None

        # /FontFile attributes
        if self.font_file is not None:
            self.lengths = [self.font_file[k] for k in FONT_LENGTHS if k in self.font_file]
            self.stream_data = self.font_obj.font_descriptor.font_file.get_data()
            self.advertised_length = sum(self.lengths)
            scanner_label = Text(self.display_title, get_label_style(FONT_FILE))
            self.binary_scanner = BinaryScanner(self.stream_data, self, scanner_label)

    def print_summary(self):
        """Prints a table of info about the font drawn from the various PDF objects. quote_type of None means all."""
        print_section_subheader(str(self), style='font.title')
        console.print(self._summary_table())
        console.line()

        if self.character_mapping:
            print_character_mapping(self)
        else:
            log.info(f"No character map found in {self}")

        if self.prepared_char_map:
            print_prepared_charmap(self)
        else:
            log.info(f"No prepared_charmap found in {self}")

        console.line()

    def _first_and_last_char(self) -> list[int]:
        return without_nones([self.font_dict.get('/FirstChar'), self.font_dict.get('/LastChar')])

    def _flag_names(self) -> list[str]:
        return [name for bit, name in FONT_FLAGS.items() if bool((self.flags or 0) & 1 << (bit - 1))]

    def _summary_table(self) -> Table:
        """Build a Rich `Table` with important info about the font"""
        table = Table(show_header=False)
        table.add_column(style='font.property', justify='right')
        table.add_column()

        def add_table_row(name, value, style: str = ''):
            value = value if isinstance(value, Text) else Text(str(value), style or get_class_style(value))
            table.add_row(name, value)

        add_table_row('Subtype', self.font_obj.sub_type)
        add_table_row('FontName', self.font_obj.name)  # TODO: is this really BaseFont?
        # add_table_row('Encoding', self.font_dict["/Encoding"])
        add_table_row('Interpretable?', self.font_obj.interpretable)
        add_table_row('bounding_box', self.font_obj.font_descriptor.bbox)
        add_table_row('/Length properties', self.lengths)
        add_table_row('/FirstChar, /LastChar', self._first_and_last_char())

        if self.flags:
            add_table_row('style flags', f"{self.flags} (" + ', '.join(self._flag_names()) + ')', 'cyan')

        add_table_row('total advertised length', self.advertised_length)

        if self.binary_scanner is not None:
            add_table_row('embedded binary length', self.binary_scanner.stream_length)
        if self.prepared_char_map is not None:
            add_table_row('prepared charmap length', len(self.prepared_char_map))
        if self.character_mapping:
            add_table_row('character mapping count', len(self.character_mapping))
        if self.widths is not None:
            for k, v in self._width_stats().items():
                add_table_row(f"char width {k}", v)

            # Check if there's a single number repeated over and over.
            if len(set(self.widths)) == 1:
                table.add_row(
                    'char widths',
                    Text(
                        f"{self.widths[0]} (single value repeated {len(self.widths)} times)",
                        style=get_class_style(list)
                    )
                )
            else:
                add_table_row('char widths', self.widths)
                add_table_row('char widths(sorted)', sorted(self.widths))

        col_0_width = max([len(entry) for entry in table.columns[0]._cells]) + 4
        table.columns[1].max_width = subheading_width() - col_0_width - 3
        return table

    def _width_stats(self):
        if self.widths is None:
            return {}

        return {
            'min': min(self.widths),
            'max': max(self.widths),
            'count': len(self.widths),
            'unique_count': len(set(self.widths)),
        }

    def __repr__(self) -> str:
        d = {}

        for f in fields(self):
            value = getattr(self, f.name)
            value = str(value) if isinstance(value, NameObject) else value

            if isinstance(value, (bytes, str)) and len(value) > MAX_REPR_STR_LEN:
                if isinstance(value, (bytes)):
                    value = value[0:MAX_REPR_STR_LEN] + b'...'
                else:
                    value = f'"{value[0:MAX_REPR_STR_LEN]}..."'
            elif isinstance(value, ArrayObject):
                value = list(value)
            elif isinstance(value, (BinaryScanner, PdfObject)):
                value = f"<{type(value).__name__} obj>"
            elif isinstance(value, Font):
                value = f'Font(name="{value.name}")'
            elif isinstance(value, str):
                value = f'"{value}"'

            #log.warning(f"{f.name} ({type(value).__name__}): {value}")
            d[f.name] = value

        return f"FontInfo(\n    " + ',\n    '.join([f"{k}={v}" for k,v in d.items()]) + '\n)'

    def __str__(self) -> str:
        return self.display_title

    @classmethod
    def extract_font_infos(cls, obj_with_resources: DictionaryObject) -> list[Self]:
        """
        Extract all the fonts from a given /Resources PdfObject node.
        obj_with_resources must have '/Resources' because that's what _cmap module expects
        """
        resources = obj_with_resources[RESOURCES].get_object()
        fonts = resources.get(FONT)

        if is_null_or_none(fonts):
            log.info(f'No fonts found in {obj_with_resources}')
            return []

        fonts = fonts.get_object()
        return [cls(label=label, font_indirect=font) for label, font in fonts.items()]

    @classmethod
    def _get_fonts_walk(cls, obj: DictionaryObject) -> list[Font]:
        """
        Get the set of all fonts (embedded and not embedded).

        If there is a key called 'BaseFont', that is a font that is used in the document.
        If there is a key called 'FontName' and another key in the same dictionary object
        that is called 'FontFilex' (where x is null, 2, or 3), then that fontname is
        embedded.

        Args:
            obj: Page resources dictionary
        """
        fonts: list[Font] = []

        def process_font(f: DictionaryObject) -> None:
            nonlocal fonts
            f = cast(DictionaryObject, f.get_object())  # to be sure

            if "/BaseFont" in f:
                fonts.append(Font.from_font_resource(f))
                fonts[-1].is_embedded = False  # TODO: should be a FontInfo prop

            if "/CharProcs" in f \
                    or ("/FontDescriptor" in f and any(x in f["/FontDescriptor"] for x in FONT_FILE_KEYS)) \
                    or ("/DescendantFonts" in f \
                        and "/FontDescriptor" in f["/DescendantFonts"][0].get_object() \
                        and any(x in f["/DescendantFonts"][0].get_object() for x in FONT_FILE_KEYS)):
                try:
                    log.warning(f"Extracting font from /CharProcs")
                    fonts.append(Font.from_font_resource(f))
                    fonts[-1].is_embedded = True
                except KeyError:
                    log.error(f"Failed to extract font from {f}")

        if "/DR" in obj and "/Font" in cast(DictionaryObject, obj["/DR"]):
            dr_obj = cast(DictionaryObject, obj["/DR"])

            for f in cast(DictionaryObject, dr_obj["/Font"]):
                log.warning(f"Extracting font from /DR")
                process_font(f)

        if "/Resources" in obj:
            resources = cast(DictionaryObject, obj["/Resources"])

            if "/Font" in resources:
                for f in cast(DictionaryObject, resources["/Font"]).values():
                    log.warning(f"Extracting font from /Resources")
                    process_font(f)

            if "/XObject" in resources:
                for x in cast(DictionaryObject, resources["/XObject"]).values():
                    xobject_fonts = cls._get_fonts_walk(cast(DictionaryObject, x.get_object()))
                    fonts.extend(xobject_fonts)

                    if xobject_fonts:
                        log.warning(f"Extracted {len(xobject_fonts)} fonts from /Resources/XObject")

        if "/Annots" in obj:
            for i, annot in enumerate(cast(ArrayObject, obj["/Annots"])):
                annots_fonts = cls._get_fonts_walk(cast(DictionaryObject, annot.get_object()))
                fonts.extend(annots_fonts)

                if annots_fonts:
                    log.warning(f"Extracted {len(annots_fonts)} fonts from /Annots[{i}]")

        if "/AP" in obj and "/N" in cast(DictionaryObject, obj["/AP"]):
            n_obj = cast(DictionaryObject, cast(DictionaryObject, obj["/AP"])["/N"])

            if n_obj.get("/Type") == "/XObject":
                n_obj_fonts = cls._get_fonts_walk(n_obj)
                fonts.extend(n_obj_fonts)

                if n_obj_fonts:
                    log.warning(f"Extracted font from /AP/N which is an /Xobject")
            else:
                for a in n_obj:
                    n_obj_dict_fonts = cls._get_fonts_walk(cast(DictionaryObject, a))
                    fonts.extend(n_obj_dict_fonts)

                    if n_obj_dict_fonts:
                        log.warning(f"Extracted {len(annots_fonts)} fonts from /AP/N/{a} (not /XObject)")

        return uniquify_fonts(fonts)


# TODO: this should probably check if the fonts are actually the same instead of just
# matching the names.
def uniquify_fonts(fonts: list[Font]) -> list[Font]:
    font_name_map = {unique_font_string(f): f for f in fonts}
    return [f for f in font_name_map.values()]


def unique_font_string(f: Font) -> str:
    font_str = f"{f.sub_type}: {f.name}"
    font_str += f" (embedded /FontFile ID: {f.font_descriptor.font_file.indirect_reference.idnum})" if f.font_descriptor.font_file else ''
    return font_str
