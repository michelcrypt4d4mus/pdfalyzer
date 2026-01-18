"""
Unify font information spread across a bunch of PdfObjects (Font, FontDescriptor,
and FontFile) into a single class.
"""
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

ATTRIBUTES_TO_SHOW_IN_SUMMARY_TABLE = [
    'sub_type',
    'base_font',
    'flags',
    'bounding_box',
]


@dataclass(kw_only=True)
class FontInfo:
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
    base_font: str = ''
    sub_type: str = ''
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
        self.base_font = f"/{self.font_obj.name}"
        self.sub_type = f"/{self.font_obj.sub_type}"
        self.widths = self.font_dict.get(WIDTHS) or self.font_dict.get(W)

        if isinstance(self.widths, IndirectObject):
            self.widths = self.widths.get_object()

        if (self.sub_type or "Unknown") == "Unknown":
            log.warning(f"Font type not given for {self.display_title}")
            self.display_title += "(UNKNOWN FONT TYPE)"
        else:
            self.display_title += f"({self.sub_type[1:]})"

        # FontDescriptor attributes
        if not is_null_or_none(self.font_obj.font_descriptor):
            self.bounding_box = self.font_obj.font_descriptor.bbox
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

    def _summary_table(self) -> Table:
        """Build a Rich `Table` with important info about the font"""
        table = Table('', '', show_header=False)
        table.columns[0].style = 'font.property'
        table.columns[0].justify = 'right'

        def add_table_row(name, value):
            table.add_row(name, Text(str(value), get_class_style(value)))

        for attr in ATTRIBUTES_TO_SHOW_IN_SUMMARY_TABLE:
            attr_value = getattr(self, attr)
            add_table_row(attr, attr_value)

        add_table_row('/Length properties', self.lengths)
        add_table_row('/FirstChar, /LastChar', self._first_and_last_char())
        add_table_row('total advertised length', self.advertised_length)

        if self.binary_scanner is not None:
            add_table_row('actual length', self.binary_scanner.stream_length)
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
        Get the set of all fonts and all embedded fonts.

        Args:
            obj: Page resources dictionary
            fnt: font
            emb: embedded fonts

        Returns:
            A tuple (fnt, emb)

        If there is a key called 'BaseFont', that is a font that is used in the document.
        If there is a key called 'FontName' and another key in the same dictionary object
        that is called 'FontFilex' (where x is null, 2, or 3), then that fontname is
        embedded.

        We create and add to two sets, fnt = fonts used and emb = fonts embedded.
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
                    log.warning(f"Extracting fonts from /Resources/XObject")
                    fonts.extend(cls._get_fonts_walk(cast(DictionaryObject, x.get_object())))

        if "/Annots" in obj:
            for i, annot in enumerate(cast(ArrayObject, obj["/Annots"])):
                log.warning(f"Extracting font from /Annots[{i}]")
                fonts.extend(cls._get_fonts_walk(cast(DictionaryObject, annot.get_object())))

        if "/AP" in obj and "/N" in cast(DictionaryObject, obj["/AP"]):
            n_obj = cast(DictionaryObject, cast(DictionaryObject, obj["/AP"])["/N"])

            if n_obj.get("/Type") == "/XObject":
                log.warning(f"Extracting font from /AP/N, /Xobject")
                fonts.extend(cls._get_fonts_walk(n_obj))
            else:
                for a in n_obj:
                    log.warning(f"Extracting fonts from /AP/N (not /XObject)")
                    fonts.extend(cls._get_fonts_walk(cast(DictionaryObject, a)))

        return uniquify_fonts(fonts)


# TODO: this should probably check if the fonts are actually the same instead of just
# matching the names.
def uniquify_fonts(fonts: list[Font]) -> list[Font]:
    font_name_map = {f.name: f for f in fonts}
    return [f for f in font_name_map.values()]
