"""
Some methods to help with the direct manipulation/processing of PyPDF2's PdfObjects
"""
from collections import namedtuple
from typing import List, Optional

from PyPDF2.generic import IndirectObject, PdfObject
from rich.markup import escape
from yaralyzer.helpers.string_helper import comma_join
from yaralyzer.util.logging import log

from pdfalyzer.output.layout import get_label_style
from pdfalyzer.util.adobe_strings import *
from pdfalyzer.util.exceptions import PdfWalkError

# For printing SymlinkNodes
SymlinkRepresentation = namedtuple('SymlinkRepresentation', ['text', 'style'])


class PdfObjectRelationship:
    """
    Simple container class for information about a link between two PDF objects.
    In the case of easy key/value pairs the reference_key and the reference_address are the same but
    for more complicated references the reference_address will be the reference_key plus sub references.

    e.g. a reference_key for a /Font labeled /F1 could be '/Resources' but the reference_address
    might be '/Resources[/Font][/F1] if the /Font is a directly embedded reference instead of a remote one.
    """
    def __init__(
            self,
            from_obj: PdfObject,
            to_obj: IndirectObject,
            reference_key: str,
            reference_address: str
        ) -> None:
        self.from_obj = from_obj
        self.to_obj = to_obj
        self.reference_key = reference_key
        self.reference_address = reference_address
        self.from_node: Optional['PdfTreeNode'] = None  # To be filled in later.  TODO: Hacky

    @classmethod
    def get_references(
            cls,
            obj: PdfObject,
            ref_key: Optional[str] = None,
            ref_address: Optional[str] = None
        ) -> List['PdfObjectRelationship']:
        """
        Recurse through elements in 'obj' and return list of PdfObjectRelationships containing all IndirectObjects
        referenced from addresses in 'obj'.
        """
        if isinstance(obj, IndirectObject):
            if ref_key is None or ref_address is None:
                raise PdfWalkError(f"{obj} is a reference but key or address not provided")
            else:
                return [cls(obj, obj, ref_key, ref_address)]

        return_list: List[PdfObjectRelationship] = []

        if isinstance(obj, list):
            for i, element in enumerate(obj):
                if not isinstance(element, (IndirectObject, list, dict)):
                    continue

                _ref_address = f"[{i}]" if ref_address is None else f"{ref_address}[{i}]"
                return_list += cls.get_references(element, ref_key or i, _ref_address)
        elif isinstance(obj, dict):
            for k, v in obj.items():
                _ref_address = k if ref_address is None else f"{ref_address}[{k}]"
                return_list += cls.get_references(v, ref_key or k, _ref_address)
        else:
            log.debug(f"Adding no references for PdfObject reference '{ref_key}' -> '{obj}'")

        for ref in return_list:
            ref.from_obj = obj

        return return_list

    def __eq__(self, other: 'PdfObjectRelationship') -> bool:
        """Note that equality does not check self.from_obj."""
        if (self.to_obj.idnum != other.to_obj.idnum) or (self.from_node != other.from_node):
            return False

        for k in ['reference_key', 'reference_address']:
            if getattr(self, k) != getattr(other, k):
                return False

        return True

    def __str__(self) -> str:
        return comma_join([f"{k}: {v}" for k, v in vars(self).items()])

    def description(self) -> str:
        """Sort of like __str__ but w/out the extra lines"""
        return f"{self.from_node}: {self.reference_address} to {self.to_obj}"


def get_symlink_representation(from_node, to_node) -> SymlinkRepresentation:
    """Returns a tuple (symlink_text, style) that can be used for pretty printing, tree creation, etc"""
    reference_key = str(to_node.get_address_for_relationship(from_node))
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


def _sort_pdf_object_refs(refs: List[PdfObjectRelationship]) -> List[PdfObjectRelationship]:
    return sorted(refs, key=lambda ref: ref.to_obj.idnum)
