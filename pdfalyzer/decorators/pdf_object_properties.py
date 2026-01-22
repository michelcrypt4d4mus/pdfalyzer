from dataclasses import dataclass, field
from typing import Any, List, Optional, Self, Union

from pypdf.errors import PdfReadError
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject, NumberObject, PdfObject
from rich.text import Text

from pdfalyzer.helpers.pdf_object_helper import pypdf_class_name
from pdfalyzer.helpers.rich_text_helper import comma_join_txt, node_label
from pdfalyzer.helpers.string_helper import INDENTED_JOINER, props_string, root_address
from pdfalyzer.output.styles.node_colors import get_class_style, get_class_style_dim
from pdfalyzer.util.adobe_strings import *
from pdfalyzer.util.logging import log, log_console, log_trace


@dataclass
class PdfObjectProperties:
    """
    Decorator for PyPDF PdfObject that extracts a couple of properties (type, label, etc).

    Attributes:
        obj (PdfObject): The underyling PDF object
        address (str | int): The location of the PDF object in the tree, e.g '/Root/Pages/Kids[0]'
        idnum (int): ID of the PDF object
        indirect_object (IndirectObject | None): IndirectObject that points to this one
        label (str): A string that meaningfully describes this object
        sub_type (str | None): The value found in the /Subtype or /S props, if it exists
        type (str | None): The value found in the /Type, defaulting to the address
    """
    obj: PdfObject
    address: str | int
    idnum: int
    indirect_object: IndirectObject | None = None

    # Computed fields
    first_address: str = field(init=False)
    label: str = field(init=False)
    sub_type: str | None = None
    type: str | None = None

    def __post_init__(self,):
        if isinstance(self.obj, DictionaryObject):
            self.type = self.obj.get(TYPE, self.address if isinstance(self.address, str) else None)
            self.sub_type = self.obj.get(SUBTYPE) or self.obj.get(S)

            if TYPE in self.obj and self.sub_type is not None:
                self.label = f"{self.type}:{self.sub_type[1:]}"
            elif self.type is None:
                self.label = "???"
                # import pdb;pdb.set_trace()
                log.warning(f"Unable to determine obj type for {self.idnum} from {self.obj}, address={self.address}!")
            else:
                self.label = self.type

            if isinstance(self.type, str):
                self.type = root_address(self.type)
                self.label = root_address(self.label)
        else:
            # If it's not a DictionaryObject all we have as far as naming is the address passed in.
            self.label = self.address
            self.type = root_address(self.address) if isinstance(self.address, str) else None  # TODO: addresses are not types

        # Force self.label to be a string. TODO this sucks.
        if isinstance(self.label, int):
            self.label = f"{UNLABELED}[{self.label}]"

        # TODO: this is hacky/temporarily incorrect bc we often don't know the parent when node is being constructed
        if isinstance(self.address, int):
            self.first_address = f"[{self.address}]"
        else:
            self.first_address = self.address

        log_trace(f"Node ID: {self.idnum}, type: {self.type}, subtype: {self.sub_type}, " +
                  f"label: {self.label}, first_address: {self.first_address}")

    @classmethod
    def from_reference(cls, ref: IndirectObject, address: str) -> Self:
        """Alternate constructor to build from an IndirectObject."""
        try:
            return cls(ref.get_object(), address, ref.idnum, ref)
        except PdfReadError as e:
            log_console.print_exception()
            log.error(f"Failed to build node because, integrity not guaranteed. Error: {e}")
            return cls(ref, address, ref.idnum)

    @classmethod
    def resolve_references(cls, reference_key: str, obj: PdfObject) -> Any:
        """Recursively build the same data structure except IndirectObjects are resolved to nodes."""
        if isinstance(obj, NumberObject):
            return obj.as_numeric()
        elif isinstance(obj, IndirectObject):
            return cls.from_reference(obj, reference_key)
        elif isinstance(obj, list):
            return [cls.resolve_references(reference_key, item) for item in obj]
        elif isinstance(obj, dict):
            return {k: cls.resolve_references(k, v) for k, v in obj.items()}
        else:
            return obj

    @classmethod
    def to_table_row(
        cls,
        reference_key: str,
        obj: PdfObject,
        is_single_row_table: bool = False
    ) -> List[Union[Text, str]]:
        """PDF object property at `reference_key` becomes a formatted 3-tuple for use in Rich tables."""
        with_resolved_refs = cls.resolve_references(reference_key, obj)

        return [
            Text(f"{reference_key}", style='grey' if isinstance(reference_key, int) else ''),
            # Prefix the Text() obj with an empty string to set unstyled chars to the class style of the object
            # they are in.
            Text('', style=get_class_style(obj)).append_text(cls._obj_to_rich_text(with_resolved_refs)),
            # 3rd col (AKA type(value)) is redundant if it's a TextString/Number/etc. node so we make it empty
            '' if is_single_row_table else Text(pypdf_class_name(obj), style=get_class_style_dim(obj))
        ]

    # TODO: this doesn't recurse...
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
            return Text(obj)
        else:
            return Text(str(obj), style=get_class_style(obj))

    def __repr__(self) -> str:
        return f"{type(self).__name__}(" + props_string(self, joiner=INDENTED_JOINER) + '\n)'

    def __rich_without_underline__(self) -> Text:
        return node_label(self.idnum, self.label, self.obj, underline=False)

    def __rich__(self) -> Text:
        return node_label(self.idnum, self.label, self.obj)

    def __str__(self) -> str:
        return self.__rich__().plain
