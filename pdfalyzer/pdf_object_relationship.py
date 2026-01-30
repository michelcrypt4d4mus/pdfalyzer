"""
Simple container class for information about a link between two PDF objects.
"""
from dataclasses import dataclass, field
from typing import Any, Self

from pypdf.generic import BooleanObject, IndirectObject, NullObject, PdfObject

from pdfalyzer.util.adobe_strings import *
from pdfalyzer.util.exceptions import PdfWalkError
from pdfalyzer.util.helpers.pdf_object_helper import coerce_nums_array_to_dict
from pdfalyzer.util.helpers.string_helper import bracketed, coerce_address, is_prefixed_by_any
from pdfalyzer.util.logging import log

INCOMPARABLE_PROPS = ['from_obj', 'to_obj']


@dataclass
class PdfObjectRelationship:
    from_node: 'PdfTreeNode'
    to_obj: IndirectObject
    reference_key: str
    address: str  # ints will be coerced to strings
    from_obj: Any | None = None
    is_child: bool = False
    is_indeterminate: bool = False
    is_link: bool = field(init=False)
    is_parent: bool = field(init=False)

    def __post_init__(self) -> None:
        """
        In the case of easy key/value pairs the reference_key and the address are the same but
        for more complicated references the address will be the reference_key plus sub references.
        e.g. a reference_key for a /Font labeled /F1 could be '/Resources' but the address
        might be '/Resources[/Font][/F1] if the /Font is a directly embedded reference instead of a remote one.
        """
        self.address = coerce_address(self.address)

        # Compute tree placement logic booleans
        if (has_indeterminate_prefix(self.from_node.type) and not isinstance(self.from_node.obj, (dict, list))) \
                or self.reference_key in INDETERMINATE_REF_KEYS:
            log.info(f"Indeterminate node {self.from_node} has relationship to {self.to_obj.idnum}")
            self.is_indeterminate = True

        self.is_link = self.reference_key in NON_TREE_KEYS or is_prefixed_by_any(self.from_node.label, LINK_NODE_KEYS)
        self.is_parent = self.reference_key == PARENT or (self.from_node.type == STRUCT_ELEM and self.reference_key == P)  # noqa: E501

        # TODO: there can be multiple OBJR refs to the same object... which wouldn't work w/this code
        if self.from_node.type == OBJR and self.reference_key == OBJ:
            log.info(f"Explicit (theoretically) child reference found for {OBJ} in {self.from_node}")
            self.is_child = True
        elif self.reference_key == KIDS or (self.from_node.type == STRUCT_ELEM and self.reference_key == K):
            self.is_child = True

        if self.is_parent and self.is_child:
            raise PdfWalkError(f"{self} is both parent->child and child->parent")

    @classmethod
    def build_node_references(
        cls,
        from_node: 'PdfTreeNode',
        from_obj: PdfObject | dict | None = None,
        ref_key: str | int | None = None,
        address: str | int | None = None
    ) -> list[Self]:
        """
        Recursively build list of relationships 'from_node.obj' contains referencing other PDF objects.
        Initially called with single arg from_node. Other args are use when recursable objs are scanned.

        Args:
            from_node (PdfTreeNode): PDF node that may contain references to other PDF objects
            from_obj (PdfObject | None): Raw PdfObject that may contain references to other PDF objects
            ref_key (str): The /Color, /Page etc. style string or int for ArrayObjects
            address (str): Base address for other refs, used for internal recursion into dicst and arrays
        """
        from_obj = from_node.obj if from_obj is None else from_obj
        references: list[Self] = []

        if isinstance(from_obj, IndirectObject):
            references.append(cls(from_node, from_obj, str(ref_key), address))
        elif isinstance(from_obj, list):
            for i, item in enumerate(from_obj):
                references += cls.build_node_references(from_node, item, ref_key or i, _build_address(i, address))
        elif isinstance(from_obj, dict):
            for key, val in from_obj.items():
                if key == NUMS and isinstance(val, list) and len(val) % 2 == 0:
                    val = coerce_nums_array_to_dict(val)

                references += cls.build_node_references(from_node, val, ref_key or key, _build_address(key, address))
        elif not isinstance(from_obj, (float, int, str, BooleanObject, NullObject)):
            log.debug(
                f"Adding no references for PdfObject reference '{ref_key}' -> '{from_obj}' ({type(from_obj).__name__})"
            )

        # Set all returned relationships to originate from top level from_obj before returning
        for ref in references:
            ref.from_obj = from_obj

        return references

    def __eq__(self, other: Self) -> bool:
        """Note that equality does not check self.from_obj equality because we don't have the idnum"""
        for key in [k for k in vars(self).keys() if k not in INCOMPARABLE_PROPS]:
            if getattr(self, key) != getattr(other, key):
                return False

        return self.from_node.idnum == other.from_node.idnum

    def __str__(self) -> str:
        s = f"Relationship of {self.from_node} to {self.to_obj.idnum}"
        s += f" (ref_key={self.reference_key}, address='{self.address}')"
        s += f" is parent/child" if self.is_parent else ''
        s += f" is child/parent" if self.is_child else ''
        s += f" via symlink" if self.is_link else ''
        return s


def _build_address(ref_key: str | int, base_address: str | int | None = None) -> str | int:
    """
    Append either array index indicators e.g. [5] or reference_keys. reference_keys that appear in a
    PDF object are left as is. Any dict keys or array indices that refere to inner objects and not
    to the PDF object itself are bracketed.  e.g. if there's a /Width key in a /Font node,
    '/Width' is the address of the font widths. But if the /Font links to the widths through a
    /Resources dict the address will be '/Resources[/Width]'
    """
    if base_address is None:
        return ref_key
    else:
        return f"{coerce_address(base_address)}{bracketed(ref_key)}"
