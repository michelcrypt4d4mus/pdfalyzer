"""
Simple container class for information about a link between two PDF objects.
"""
from typing import List, Optional, Union

from PyPDF2.generic import IndirectObject, PdfObject
from yaralyzer.helpers.string_helper import comma_join
from yaralyzer.util.logging import log

from pdfalyzer.util.adobe_strings import *
from pdfalyzer.util.exceptions import PdfWalkError


class PdfObjectRelationship:
    """
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
            ref_key: Optional[Union[str, int]] = None,
            ref_address: Optional[Union[str, int]] = None
        ) -> List['PdfObjectRelationship']:
        """
        Recurse through elements in 'obj' and return list of PdfObjectRelationships containing all IndirectObjects
        referenced from addresses in 'obj'.
        """
        if isinstance(obj, IndirectObject):
            if ref_key is None or ref_address is None:
                raise PdfWalkError(f"{obj} is a reference but key or address not provided")
            else:
                return [cls(obj, obj, str(ref_key), str(ref_address))]

        return_list: List[PdfObjectRelationship] = []

        if isinstance(obj, list):
            for i, element in enumerate(obj):
                if not isinstance(element, (IndirectObject, list, dict)):
                    continue

                idx = f"[{i}]"
                _ref_address = idx if ref_address is None else f"{ref_address}{idx}"
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
