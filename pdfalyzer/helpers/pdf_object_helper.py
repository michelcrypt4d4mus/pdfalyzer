"""
Some methods to help with the direct manipulation/processing of PyPDF2's PdfObjects
"""
from collections import namedtuple
from typing import List

from PyPDF2.generic import IndirectObject, PdfObject
from rich.markup import escape
from yaralyzer.util.logging import log

from pdfalyzer.util.adobe_strings import DANGEROUS_PDF_KEYS
from pdfalyzer.util.exceptions import PdfWalkError
from pdfalyzer.helpers.rich_text_helper import get_label_style

# In the case of easy key/value pairs the reference_key and the reference_address are the same but
# for more complicated references the reference_address will be the reference_key plus sub references.
#
#   e.g. a reference_key for a /Font labeled /F1 could be '/Resources' but the reference_address
# might be '/Resources[/Font][/F1] if the /Font is a directly embedded reference instead of a remote one.
PdfObjectRef = namedtuple('PdfObjectRef', ['reference_key', 'reference_address', 'pdf_obj'])

# For printing SymlinkNodes
SymlinkRepresentation = namedtuple('SymlinkRepresentation', ['text', 'style'])


def get_references(obj: PdfObject, ref_key=None, ref_address=None) -> List[PdfObjectRef]:
    """Return list of PdfObjectRefs"""
    if isinstance(obj, IndirectObject):
        if ref_key is None or ref_address is None:
            raise PdfWalkError(f"{obj} is a reference but key or address not provided")

        return [PdfObjectRef(ref_key, ref_address, obj)]
    elif isinstance(obj, list) and isinstance(obj, dict):
        raise PdfWalkError(f"PdfObject {obj} is both a dict and a list")

    return_list = []

    if isinstance(obj, list):
        for i, element in enumerate(obj):
            if not isinstance(element, (IndirectObject, list, dict)):
                continue

            _ref_address = f"[{i}]" if ref_address is None else f"{ref_address}[{i}]"
            return_list += get_references(element, ref_key or i, _ref_address)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            _ref_address = k if ref_address is None else f"{ref_address}[{k}]"
            return_list += get_references(v, ref_key or k, _ref_address)
    else:
        log.debug(f"Adding no references for PdfObject reference '{ref_key}' -> '{obj}'")

    return return_list


def get_symlink_representation(from_node, to_node) -> SymlinkRepresentation:
    """Returns a tuple (symlink_text, style) that can be used for pretty printing, tree creation, etc"""
    reference_key = str(to_node.get_reference_key_for_relationship(from_node))
    pdf_instruction = reference_key.split('[')[0]  # In case we ended up with a [0] or similar

    if pdf_instruction in DANGEROUS_PDF_KEYS:
        symlink_style = 'red_alert'
    else:
        symlink_style = get_label_style(to_node.label) + ' dim'

    symlink_str = f"{escape(reference_key)} [bright_white]=>[/bright_white]"
    symlink_str += f" {escape(str(to_node.target))} [grey](Non Child Reference)[/grey]"
    return SymlinkRepresentation(symlink_str, symlink_style)


def pdf_object_id(pdf_object):
    """Return the ID of an IndirectObject and None for everything else"""
    return pdf_object.idnum if isinstance(pdf_object, IndirectObject) else None


def does_list_have_any_references(_list) -> bool:
    """Return true if any element of _list is an IndirectObject"""
    return any(isinstance(item, IndirectObject) for item in _list)
