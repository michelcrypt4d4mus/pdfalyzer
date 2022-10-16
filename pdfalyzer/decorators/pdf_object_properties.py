"""
Decorator for PyPDF2 PdfObject that extracts a couple of properties (type, label, etc).
"""
from typing import Any, List, Optional, Union

from PyPDF2.generic import DictionaryObject, IndirectObject, NumberObject, PdfObject
from rich.markup import escape
from rich.text import Text

from pdfalyzer.helpers.pdf_object_helper import pypdf_class_name
from pdfalyzer.helpers.rich_text_helper import get_label_style, get_type_style, get_type_string_style
from pdfalyzer.helpers.string_helper import root_address
from pdfalyzer.output.pdf_node_rich_table import get_node_type_style
from pdfalyzer.util.adobe_strings import *


class PdfObjectProperties:
    """Simple class to extract critical features of a PdfObject."""
    def __init__(
            self,
            pdf_object: PdfObject,
            address: str,
            idnum: int,
            indirect_object: Optional[IndirectObject] = None
        ):
        self.idnum = idnum
        self.obj = pdf_object
        self.indirect_object = indirect_object
        self.sub_type = None
        self.all_references_processed = False
        self.known_to_parent_as: Optional[str] = None

        if isinstance(pdf_object, DictionaryObject):
            self.type = pdf_object.get(TYPE) or address
            self.sub_type = pdf_object.get(SUBTYPE) or pdf_object.get(S)

            if TYPE in pdf_object and self.sub_type is not None:
                self.label = f"{self.type}:{self.sub_type[1:]}"
            else:
                self.label = self.type

            if isinstance(self.type, str):
                self.type = root_address(self.type)
                self.label = root_address(self.label)
        else:
            # If it's not a DictionaryObject all we have as far as naming is the address passed in.
            self.label = address
            self.type = root_address(address) if isinstance(address, str) else None

        # Force a string. TODO this sucks.
        if isinstance(self.label, int):
            self.label = f"{UNLABELED}[{self.label}]"

        # TODO: this is hacky/temporarily incorrect bc we often don't know the parent when node is being constructed
        if isinstance(address, int):
            self.first_address = f"[{address}]"
        else:
            self.first_address = address

    @classmethod
    def from_reference(cls, reference: IndirectObject, address: str) -> 'PdfObjectProperties':
        return cls(reference.get_object(), address, reference.idnum, reference)

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
        """PDF object property at reference_key becomes a formatted 3-tuple for use in Rich tables."""
        return [
            Text(f"{reference_key}", style='grey' if isinstance(reference_key, int) else ''),
            Text(f"{escape(str(cls.resolve_references(reference_key, obj)))}", style=get_type_style(type(obj))),
            # 3rd col (AKA type(value)) is redundant if it's a TextString/Number/etc. node so we make it empty
            '' if is_single_row_table else Text(pypdf_class_name(obj), style=get_type_string_style(type(obj)))
        ]

    def __rich__(self) -> Text:
        return node_label(self.idnum, self.label, self.obj)

    def __str__(self) -> str:
        return self.__rich__().plain


def node_label(idnum: int, label: str, pdf_object: PdfObject) -> Text:
    """Colored text representation of a node."""
    text = Text('<', style='white')
    text.append(f'{idnum}', style='bright_white')
    text.append(':', style='white')
    text.append(label[1:], style=f'{get_label_style(label)} underline bold')
    text.append('(', style='white')
    text.append(pypdf_class_name(pdf_object), style=get_node_type_style(pdf_object))
    text.append(')', style='white')
    text.append('>')
    return text
