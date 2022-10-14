"""
Some methods to help with the direct manipulation/processing of PyPDF2's PdfObjects
"""
from typing import List, Optional

from PyPDF2.generic import IndirectObject, PdfObject
from rich.text import Text

from pdfalyzer.helpers.string_helper import pypdf_class_name
from pdfalyzer.output.layout import get_label_style
from pdfalyzer.output.pdf_node_rich_table import get_node_type_style
from pdfalyzer.pdf_object_relationship import PdfObjectRelationship
from pdfalyzer.util.adobe_strings import *


def pdf_object_id(pdf_object) -> Optional[int]:
    """Return the ID of an IndirectObject and None for everything else"""
    return pdf_object.idnum if isinstance(pdf_object, IndirectObject) else None


def does_list_have_any_references(_list) -> bool:
    """Return true if any element of _list is an IndirectObject."""
    return any(isinstance(item, IndirectObject) for item in _list)


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


def _sort_pdf_object_refs(refs: List[PdfObjectRelationship]) -> List[PdfObjectRelationship]:
    return sorted(refs, key=lambda ref: ref.to_obj.idnum)
