"""
PDF object decorator - wraps actual PDF objects to make them anytree nodes.
Also adds decorators/generators for Rich text representation.

Child/parent relationships should be set using the add_child()/set_parent()
methods and not set directly. (TODO: this could be done better with anytree
hooks)
"""
from typing import List, Optional, Union

from anytree import NodeMixin
from PyPDF2.errors import PdfReadError
from PyPDF2.generic import DictionaryObject, IndirectObject, NumberObject, PdfObject, StreamObject
from rich.markup import escape
from rich.text import Text
from yaralyzer.output.rich_console import console
from yaralyzer.util.logging import log

from pdfalyzer.helpers.pdf_object_helper import node_label
from pdfalyzer.helpers.rich_text_helper import get_type_string_style, get_type_style
from pdfalyzer.helpers.string_helper import pypdf_class_name, root_address
from pdfalyzer.pdf_object_relationship import PdfObjectRelationship
from pdfalyzer.util.adobe_strings import *
from pdfalyzer.util.exceptions import PdfWalkError

DEFAULT_MAX_ADDRESS_LENGTH = 90
DECODE_FAILURE_LEN = -1


class PdfTreeNode(NodeMixin):
    def __init__(self, obj: PdfObject, address: str, idnum: int):
        """
        address: PDF instruction string + modifiers used to reference obj
        idnum: ID used in the reference
        """
        self.obj = obj
        self.idnum = idnum
        self.all_references_processed: bool = False
        self.other_relationships: List[PdfObjectRelationship] = []
        self.sub_type = None

        if isinstance(obj, DictionaryObject):
            self.type = obj.get(TYPE) or address
            self.sub_type = obj.get(SUBTYPE) or obj.get(S)
            self.label = obj.get(TYPE) or address  # TODO: should we use sub_type?

            if isinstance(self.type, str):
                self.type = root_address(self.type)
        elif isinstance(address, int):
            self.label = f"{UNLABELED}[{address}]"
            self.type = str(address)
        else:
            self.label = address
            self.type = root_address(address)

        # TODO: this is hacky/temporarily incorrect bc we often don't know the parent when node is being constructed
        if isinstance(address, int):
            self.known_to_parent_as = f"[{address}]"
        else:
            self.known_to_parent_as = address

        if isinstance(obj, StreamObject):
            try:
                self.stream_data = self.obj.get_data()
                self.stream_length = len(self.stream_data)
            except PdfReadError as e:
                msg = f"Failed to decode stream in {self}: {e}"
                console.print_exception()
                log.warning(msg)
                self.stream_data = msg.encode()
                self.stream_length = DECODE_FAILURE_LEN
        else:
            self.stream_data = None
            self.stream_length = 0

    @classmethod
    def from_reference(cls, ref: IndirectObject, address: str) -> 'PdfTreeNode':
        """Builds a PdfTreeDecorator from an IndirectObject"""
        return cls(ref.get_object(), address, ref.idnum)

    @classmethod
    def resolve_references(cls, reference_key: str, obj: PdfObject):
        """
        Recursively build the same data structure except IndirectObjects are resolved to nodes.
        TODO: pdf_object_helper.py is a much better location for this but creates a circular reference.
        """
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
    def to_table_row(cls, reference_key: str, obj: PdfObject, is_single_row_table=False) -> List[Union[Text, str]]:
        """
        Turns PDF object properties into a formatted 3-tuple for use in Rich tables representing PdfObjects.
        TODO: pdf_object_helper.py is a much better location for this but creates a circular reference.
        """
        return [
            Text(f"{reference_key}", style='grey' if isinstance(reference_key, int) else ''),
            Text(f"{escape(str(cls.resolve_references(reference_key, obj)))}", style=get_type_style(type(obj))),
            # 3rd col (AKA type(value)) is redundant if it's a TextString/Number/etc. node so we make it empty
            '' if is_single_row_table else Text(pypdf_class_name(obj), style=get_type_string_style(type(obj)))
        ]

    def set_parent(self, parent: 'PdfTreeNode') -> None:
        """Set the parent of this node"""
        if self.parent and self.parent != parent:
            raise PdfWalkError(f"Cannot set {parent} as parent of {self}, parent is already {self.parent}")

        self.parent = parent
        self.remove_relationship(parent)
        # Adjust incorrect known_to_parent_as that can arise when adding non tree references to the walker
        self.known_to_parent_as = self._find_address_of_this_node(parent) or self.known_to_parent_as
        log.info(f"  Added {parent} as parent of {self}")

    def add_child(self, child: 'PdfTreeNode') -> None:
        """Add a child to this node"""
        existing_child = next((c for c in self.children if c.idnum == child.idnum), None)

        if existing_child is not None:
            if existing_child == child:
                log.debug(f"{child} is already child of {self}")
                return
            else:
                raise PdfWalkError(f"{self} already has child w/this ID: {child}")

        self.children += (child,)
        child.remove_relationship(self)
        # Adjust incorrect known_to_parent_as that can arise when adding non tree references to the walker
        child.known_to_parent_as = child._find_address_of_this_node(self) or child.known_to_parent_as
        log.info(f"  Added {child} as child of {self}")

    def add_relationship(self, relationship: PdfObjectRelationship) -> None:
        """Add a relationship that points at this node's PDF object. TODO: doesn't include parent/child"""
        if relationship in self.other_relationships:
            log.debug(f"{relationship.description()} already in {self}'s other relationships")
            self.print_other_relationships()
            return

        log.info(f'Adding other relationship: {relationship.description()} pointing to {self}')
        self.other_relationships.append(relationship)

    def remove_relationship(self, from_node: 'PdfTreeNode') -> None:
        """Remove all other_relationships from from_node to this node"""
        relationships_to_remove = [r for r in self.other_relationships if r.from_node == from_node]

        if len(relationships_to_remove) == 0:
            return
        elif len(relationships_to_remove) > 1 and not all(r.reference_key in [FIRST, LAST] for r in relationships_to_remove):
            log.warning(f"> 1 relationships to remove from {from_node} to {self}: {relationships_to_remove}")

        for relationship in relationships_to_remove:
            log.debug(f"Removing relationship {relationship} from {self}")
            self.other_relationships.remove(relationship)

    def other_relationship_count(self) -> int:
        return len(self.other_relationships)

    def get_address_for_relationship(self, from_node: 'PdfTreeNode') -> str:
        """Get the label that links from_node to this one outside of the tree structure"""
        relationship = next((r for r in self.other_relationships if r.from_node == from_node), None)

        if relationship is None:
            raise PdfWalkError(f"Can't find other relationship from {from_node} to {self}")

        return relationship.reference_address

    # TODO: this doesn't include /Parent references
    def referenced_by_keys(self) -> List[str]:
        """All the PDF instruction strings that referred to this object"""
        return [r.reference_key for r in self.other_relationships] + [self.known_to_parent_as]

    def is_parent_reference(self, reference_key: str) -> bool:
        """Returns True for explicit parent references."""
        if reference_key == PARENT or (self.type == STRUCT_ELEM and reference_key == P):
            log.debug(f"Explicit parent reference in {self} at {reference_key}")
            return True
        else:
            return False

    def is_child_reference(self, reference_key: str) -> bool:
        """Returns True for explicit child references."""
        if reference_key == KIDS or (self.type == STRUCT_ELEM and reference_key == K):
            log.debug(f"Explicit child reference in {self} at {reference_key}")
            return True
        elif self.type == OBJR and reference_key == OBJ:
            # TODO: there can be multiple OBJR refs to the same object... which wouldn't work w/this code
            log.info(f"Explicit (theoretically) child reference found for {OBJ} in {self}")
            return True
        else:
            return False

    def is_indeterminate_reference(self, reference_key) -> bool:
        """Returns true if we need to wait for all objects to be parsed before placement."""
        if reference_key in INDETERMINATE_REFERENCES:
            return True
        else:
            return False

    def is_pure_reference(self, reference_key: str) -> bool:
        """Returns True if the reference is a pure reference/bookmark style node and thus not in the tree."""
        if reference_key in (NON_TREE_REFERENCES + PURE_REFERENCE_NODE_LABELS):
            return True

        # TODO: Checking startswith(NUMS) etc. is a hack that probably will not cover all cases with /StructElem
        return any(self.label.startswith(key) for key in PURE_REFERENCE_NODE_LABELS)

    def references(self) -> List[PdfObjectRelationship]:
        """Returns all nodes referenced from this node (see PdfObjectRelationship definition)"""
        refs = PdfObjectRelationship.get_references(self.obj)

        for ref in refs:
            ref.from_node = self

        return refs

    def contains_stream(self) -> bool:
        """Returns True for ContentStream, DecodedStream, and EncodedStream objects"""
        return isinstance(self.obj, StreamObject)

    def _find_address_of_this_node(self, from_node: 'PdfTreeNode') -> Optional[str]:
        """Find the address used in from_node to refer to this node"""
        refs_to_this_node = [ref for ref in from_node.references() if ref.to_obj.idnum == self.idnum]

        if len(refs_to_this_node) == 1:
            return refs_to_this_node[0].reference_address
        elif len(refs_to_this_node) == 0:
            # TODO: Hack city. /XRef streams are basically trailer nodes without any direct reference
            if self.parent and self.parent.label == TRAILER and self.type == XREF and XREF_STREAM in self.parent.obj:
                return XREF_STREAM
            elif self.label not in [FIRST, LAST, NEXT, PREV]:
                log.warning(f"Could not find expected reference from {from_node} to {self}")
                return None
        else:
            reference_address = refs_to_this_node[0].reference_address

            if not all(ref.reference_address in [FIRST, LAST] for ref in refs_to_this_node):
                msg = f"Multiple refs from {from_node} to {self}: {refs_to_this_node}"
                log.warning(msg + ", using {reference_address}")

            return reference_address

    ######################################
    # BELOW HERE IS JUST TEXT FORMATTING #
    ######################################

    def print_other_relationships(self) -> None:
        """Print this node's non tree relationships (the ones represented by SymlinkNodes in the tree)"""
        console.print(f"Other relationships of {escape(str(self))}")

        for r in self.other_relationships:
            console.print(f"  Referenced as {escape(str(r.reference_key))} by {escape(str(r.from_node))}")

    def tree_address(self, max_length: Optional[int] = None) -> str:
        """Creates a string like '/Catalog/Pages/Resources/Font' truncated to max_length (if given)"""
        if self.label == TRAILER:
            return '/'

        address = ''.join([str(node.known_to_parent_as) for node in self.path if node.label != TRAILER])

        if max_length is None or max_length > len(address):
            return address

        return '...' + address[-max_length:][3:]

    def _node_label(self) -> Text:
        return node_label(self.idnum, self.label, self.obj)

    def _colored_address(self, max_length: Optional[int] = None) -> Text:
        """Rich text version of tree_address()"""
        text = Text('@', style='bright_white')
        text.append(self.tree_address(max_length), style='address')
        return text

    def __rich__(self) -> Text:
        return self._node_label()[:-1] + self._colored_address(max_length=DEFAULT_MAX_ADDRESS_LENGTH) + Text('>')

    def __str__(self) -> str:
        return self._node_label().plain

    def __repr__(self) -> str:
        return self.__str__()
