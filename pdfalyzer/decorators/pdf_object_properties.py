from dataclasses import dataclass
from typing import Any, Self

from pypdf.errors import PdfReadError
from pypdf.generic import DictionaryObject, IndirectObject, NullObject, NumberObject, PdfObject
from rich.text import Text
from yaralyzer.util.helpers.env_helper import log_console
from yaralyzer.util.logging import log_trace

from pdfalyzer.output.highlighter import PdfHighlighter
from pdfalyzer.output.theme import (COMPLETE_THEME_DICT, DEFAULT_LABEL_STYLE, get_class_style,
     get_class_style_dim, get_class_style_italic)
from pdfalyzer.util.adobe_strings import GO_TO_E, GO_TO_R, IMAGE, S, SUBTYPE, TYPE, UNLABELED, XOBJECT
from pdfalyzer.util.helpers.pdf_object_helper import pypdf_class_name
from pdfalyzer.util.helpers.rich_helper import comma_join_txt
from pdfalyzer.util.helpers.string_helper import coerce_address, is_array_idx, props_string_indented, root_address
from pdfalyzer.util.logging import highlight, log, log_highlighter, pdf_highlighter


@dataclass
class PdfObjectProperties:
    """
    Decorator for PyPDF PdfObject that extracts a couple of properties (type, label, etc).

    Attributes:
        obj (PdfObject): The underyling PDF object
        address (str | int): The location of the PDF object in its parent object, e.g 'Kids[0]'
        idnum (int): ID of the PDF object
        indirect_object (IndirectObject | None): IndirectObject that points to this one
        label (str): A string that meaningfully describes this object
        sub_type (str | None): The value found in the /Subtype or /S props, if it exists
        type (str | None): The value found in the /Type, defaulting to the address
    """
    obj: PdfObject
    address: str  # ints will be coerced
    idnum: int
    indirect_object: IndirectObject | None = None

    # Computed fields
    label: str = ''
    sub_type: str | None = None
    _type: str | None = None

    @property
    def type(self) -> str:
        return self._type or '???'

    @property
    def label_style(self) -> str:
        type_no_slash = self.type.removeprefix('/')
        sub_type = self.sub_type or ''

        if sub_type.startswith(GO_TO_R) or sub_type.startswith(GO_TO_E):
            return COMPLETE_THEME_DICT[PdfHighlighter.prefixed_style(GO_TO_R)]
        elif self.type == XOBJECT and sub_type == IMAGE:
            return COMPLETE_THEME_DICT[PdfHighlighter.prefixed_style(IMAGE)]

        return COMPLETE_THEME_DICT.get(PdfHighlighter.prefixed_style(type_no_slash), DEFAULT_LABEL_STYLE)

    @type.setter
    def type(self, _type: str | None):
        self._type = _type

        if self._type is None:
            log.warning(f"Unable to determine obj type for {self.idnum}, address={self.address}, obj={self.obj}!")
            self.label = f"{UNLABELED}{self.address}"
        elif self.sub_type is not None:
            self.label = f"{self.type}:{self.sub_type[1:]}"
        else:
            self.label = self._type

    def __post_init__(self,):
        self.address = coerce_address(self.address)

        if isinstance(self.obj, DictionaryObject):
            self._type = self.obj.get(TYPE)
            self.sub_type = self.obj.get(SUBTYPE) or self.obj.get(S)
        elif isinstance(self.obj, NullObject):
            self._type = NullObject.__name__

        # Use address as type if no explicit /Type, e.g. obj referenced as '/Font' is considered a /Font type.
        self.type = self._type or (root_address(self.address) if not is_array_idx(self.address) else None)
        log_trace(f"Built {repr(self)}")

    @classmethod
    def from_reference(cls, ref: IndirectObject, address: str | int) -> Self:
        """Alternate constructor to build from an IndirectObject."""
        try:
            return cls(ref.get_object(), address, ref.idnum, ref)
        except PdfReadError as e:
            log_console.print_exception()
            log.error(f"Failed to build node because, integrity not guaranteed. Error: {e}")
            return cls(ref, address, ref.idnum)

    def get_table_row(
        self,
        reference_key: str | int | None,
        pdfalyzer: 'Pdfalyzer',  # noqa: F821
        empty_3rd_col: bool = False
    ) -> tuple[Text, Text, Text]:
        """Extract property at `reference_key` and build a formatted 3-tuple for use in Rich tables."""
        if reference_key is None:
            key_style = ''
            row_obj = self.obj
        else:
            if isinstance(self.obj, dict):
                row_obj = self.obj.get(reference_key)  # NOTE: self.obj[k] turns IndirectObjects into PdfObjects!
            elif isinstance(self.obj, list) and isinstance(reference_key, int):
                row_obj = self.obj[reference_key]
            else:
                raise Exception(f"Invalid ref key/obj combo! ref_key={reference_key}, obj={repr(self)}")

            if isinstance(reference_key, int):
                key_style = 'grey'
            else:
                key_style = pdf_highlighter.get_style(reference_key) or log_highlighter.get_style(reference_key)

        with_resolved_refs = self._resolve_references(reference_key, row_obj, pdfalyzer)
        value_style = key_style if isinstance(row_obj, str) else get_class_style(row_obj)
        col1 = Text(f"{reference_key}", style=key_style)
        # Prefix the Text() with empty string to set unstyled chars to style of the object they are in.
        col2 = Text('', style=value_style).append_text(self._obj_to_rich_text(with_resolved_refs))
        col3 = Text('' if empty_3rd_col else pypdf_class_name(row_obj), style=get_class_style_dim(row_obj))
        return (col1, col2, col3)

    def node_label(self, underline: bool = True) -> Text:
        """Colored text representation of a PDF node. Example: <5:FontDescriptor(Dictionary)>."""
        text = Text('<', style='white')
        text.append(f'{self.idnum}', style='bright_white')
        text.append(':', style='white')
        text.append(self.label[1:], style=f"bold {self.label_style} {'underline' if underline else ''}")
        text.append('(', style='white')
        text.append(pypdf_class_name(self.obj), style=get_class_style_italic(self.obj))
        text.append(')', style='white')
        text.append('>')
        return text

    def _resolve_references(self, reference_key: str | int, obj: PdfObject, pdfalyzer: 'Pdfalyzer') -> Any:  # noqa: F821,E501
        """Recursively build the same data structure except IndirectObjects are resolved to nodes."""
        if isinstance(obj, NumberObject):
            return obj.as_numeric()
        elif isinstance(obj, IndirectObject):
            node = pdfalyzer.find_node_by_idnum(obj.idnum)
            return node.pdf_object if node else self.from_reference(obj, reference_key)
        elif isinstance(obj, dict):
            return {k: self._resolve_references(k, v, pdfalyzer) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._resolve_references(reference_key, item, pdfalyzer) for item in obj]
        else:
            return obj

    # TODO: this doesn't recurse?
    @classmethod
    def _obj_to_rich_text(cls, obj: Any) -> Text:
        """Recurse through `obj` and build a `Text` object."""
        if isinstance(obj, dict):
            key_value_pairs = [Text(f"{k}: ").append_text(cls._obj_to_rich_text(v)) for k, v in obj.items()]
            return Text('{').append_text(comma_join_txt(key_value_pairs)).append('}')
        elif isinstance(obj, list):
            items = [cls._obj_to_rich_text(item) for item in obj]
            return Text('[').append_text(comma_join_txt(items)).append(']')
        else:
            return cls._to_text(obj)

    @classmethod
    def _to_text(cls, obj: Any) -> Text:
        """Handles styling non-recursable objects."""
        if isinstance(obj, cls):
            return cls.__rich_without_underline__(obj)
        elif isinstance(obj, str):
            if 'http' in obj or obj.startswith('/'):
                return highlight(obj)
            else:
                return Text(obj)
        else:
            return Text(str(obj), style=get_class_style(obj))

    def __repr__(self) -> str:
        return f"{type(self).__name__}(" + props_string_indented(self) + '\n)'

    def __rich_without_underline__(self) -> Text:
        return self.node_label(underline=False)

    def __rich__(self) -> Text:
        return self.node_label()

    def __str__(self) -> str:
        return self.__rich__().plain
