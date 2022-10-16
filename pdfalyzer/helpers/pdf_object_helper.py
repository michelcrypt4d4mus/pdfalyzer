"""
Some methods to help with the direct manipulation/processing of PyPDF2's PdfObjects
"""
import re
from typing import Any, List, Optional, Union

from PyPDF2.generic import IndirectObject
from yaralyzer.util.logging import log

from pdfalyzer.helpers.string_helper import is_prefixed_by_any, replace_digits
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


def has_indeterminate_prefix(address: str) -> bool:
    return is_prefixed_by_any(address, INDETERMINATE_PREFIXES)


def have_same_non_digit_chars(addresses: List[str]) -> bool:
    """Returns true if string addresses are same except for digits."""
    digits_to_Xes = set([replace_digits(a) for a in addresses])
    log.info(f"Digits to Xes: {digits_to_Xes}")
    return len(digits_to_Xes) == 1
