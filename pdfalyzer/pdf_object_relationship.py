"""
Simple container class for information about a link between two PDF objects.
"""
from typing import List, Optional, Union

from pypdf.generic import IndirectObject, PdfObject
from yaralyzer.util.logging import log

from pdfalyzer.helpers.string_helper import bracketed, is_prefixed_by_any
from pdfalyzer.util.adobe_strings import *

INCOMPARABLE_PROPS = ['from_obj', 'to_obj']


class PdfObjectRelationship:
    def __init__(
            self,
            from_node: 'PdfTreeNode',
            to_obj: IndirectObject,
            reference_key: str,
            address: str
        ) -> None:
        """
        In the case of easy key/value pairs the reference_key and the address are the same but
        for more complicated references the address will be the reference_key plus sub references.
        e.g. a reference_key for a /Font labeled /F1 could be '/Resources' but the address
        might be '/Resources[/Font][/F1] if the /Font is a directly embedded reference instead of a remote one.
        """
        self.from_node = from_node
        self.to_obj = to_obj
        self.reference_key = reference_key
        self.address = address

        # Compute tree placement logic booleans
        if (has_indeterminate_prefix(from_node.type) and not isinstance(self.from_node.obj, dict)) \
                or reference_key in INDETERMINATE_REF_KEYS:
            log.info(f"Indeterminate node: {from_node}")
            self.is_indeterminate = True
        else:
            self.is_indeterminate = False

        self.is_link = reference_key in NON_TREE_KEYS or is_prefixed_by_any(from_node.label, LINK_NODE_KEYS)
        self.is_parent = reference_key == PARENT or (from_node.type == STRUCT_ELEM and reference_key == P)

        # TODO: there can be multiple OBJR refs to the same object... which wouldn't work w/this code
        if from_node.type == OBJR and reference_key == OBJ:
            log.info(f"Explicit (theoretically) child reference found for {OBJ} in {from_node}")
            self.is_child = True
        elif reference_key == KIDS or (from_node.type == STRUCT_ELEM and reference_key == K):
            self.is_child = True
        else:
            self.is_child = False

    @classmethod
    def build_node_references(
            cls,
            from_node: 'PdfTreeObject',
            from_obj: Optional[PdfObject] = None,
            ref_key: Optional[Union[str, int]] = None,
            address: Optional[str] = None
        ) -> List['PdfObjectRelationship']:
        """
        Builds list of relationships 'from_node.obj' contains referencing other PDF objects.
        Initially called with single arg from_node. Other args are employed when recursable
        types (i.e. list, dict) are recursively scanned.
        """
        if from_node is None and from_obj is None:
            raise ValueError("Either :from_node or :from_obj must be provided to get references")

        from_obj = from_node.obj if from_obj is None else from_obj
        references: List[PdfObjectRelationship] = []

        if isinstance(from_obj, IndirectObject):
            references.append(cls(from_node, from_obj, str(ref_key), str(address)))
        elif isinstance(from_obj, list):
            for i, item in enumerate(from_obj):
                references += cls.build_node_references(from_node, item, ref_key or i, _build_address(i, address))
        elif isinstance(from_obj, dict):
            for key, val in from_obj.items():
                references += cls.build_node_references(from_node, val, ref_key or key, _build_address(key, address))
        else:
            log.debug(f"Adding no references for PdfObject reference '{ref_key}' -> '{from_obj}'")

        # Set all returned relationships to originate from top level from_obj before returning
        for ref in references:
            ref.from_obj = from_obj

        return references

    def __eq__(self, other: 'PdfObjectRelationship') -> bool:
        """Note that equality does not check self.from_obj equality because we don't have the idnum"""
        for key in [k for k in vars(self).keys() if k not in INCOMPARABLE_PROPS]:
            if getattr(self, key) != getattr(other, key):
                return False

        return self.from_node.idnum == other.from_node.idnum

    def __str__(self) -> str:
        return f"{self.from_node} ref_key: {self.reference_key}, addr: {self.address} => nodeID {self.to_obj.idnum}"


def _build_address(ref_key: Union[str, int], base_address: Optional[str] = None) -> str:
    """
    Append either array index indicators e.g. [5] or reference_keys. reference_keys that appear in a
    PDF object are left as is. Any dict keys or array indices that refere to inner objects and not
    to the PDF object itself are bracketed.  e.g. if there's a /Width key in a /Font node,
    '/Width' is the address of the font widths. But if the /Font links to the widths through a
    /Resources dict the address will be '/Resources[/Width]'
    """
    bracketed_ref_key = bracketed(ref_key)

    if isinstance(ref_key, int):
        return bracketed_ref_key if base_address is None else f"{base_address}{bracketed_ref_key}"
    else:    # Don't bracket the reference keys that appear in the PDF objects themselves
        return ref_key if base_address is None else f"{base_address}{bracketed_ref_key}"
