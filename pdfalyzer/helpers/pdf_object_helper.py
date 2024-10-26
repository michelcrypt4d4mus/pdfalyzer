"""
Some methods to help with the direct manipulation/processing of PyPDF's PdfObjects
"""
from typing import List, Optional

from pypdf.generic import IndirectObject, PdfObject

from pdfalyzer.pdf_object_relationship import PdfObjectRelationship
from pdfalyzer.util.adobe_strings import *


def pdf_object_id(pdf_object) -> Optional[int]:
    """Return the ID of an IndirectObject and None for everything else"""
    return pdf_object.idnum if isinstance(pdf_object, IndirectObject) else None


def does_list_have_any_references(_list) -> bool:
    """Return true if any element of _list is an IndirectObject."""
    return any(isinstance(item, IndirectObject) for item in _list)


def _sort_pdf_object_refs(refs: List[PdfObjectRelationship]) -> List[PdfObjectRelationship]:
    return sorted(refs, key=lambda ref: ref.to_obj.idnum)


def pypdf_class_name(obj: PdfObject) -> str:
    """Shortened name of type(obj), e.g. PyPDF.generic._data_structures.ArrayObject becomes Array"""
    class_pkgs = type(obj).__name__.split('.')
    class_pkgs.reverse()
    return class_pkgs[0].removesuffix('Object')
