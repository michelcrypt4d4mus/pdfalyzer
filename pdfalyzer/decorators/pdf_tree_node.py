"""
PDF node decorator - wraps actual PDF objects to make them anytree nodes.
Also adds decorators/generators for Rich text representation.

Child/parent relationships should be set using the add_child()/set_parent()
methods and not set directly. (TODO: this could be done better with anytree
hooks)
"""
from typing import Callable, List, Optional, Set

from anytree import NodeMixin
from PyPDF2.errors import PdfReadError
from PyPDF2.generic import IndirectObject, PdfObject, StreamObject
from rich.markup import escape
from rich.text import Text
from yaralyzer.helpers.string_helper import comma_join
from yaralyzer.output.rich_console import console
from yaralyzer.util.logging import log

from pdfalyzer.decorators.pdf_object_properties import PdfObjectProperties
from pdfalyzer.helpers.string_helper import is_prefixed_by_any
from pdfalyzer.pdf_object_relationship import PdfObjectRelationship
from pdfalyzer.util.adobe_strings import *
from pdfalyzer.util.exceptions import PdfWalkError

DEFAULT_MAX_ADDRESS_LENGTH = 90
DECODE_FAILURE_LEN = -1


class PdfTreeNode(NodeMixin, PdfObjectProperties):
    def __init__(self, obj: PdfObject, address: str, idnum: int):
        """
        obj: The underlying PDF object
        address: the first address that points from some node to this one
        idnum: ID used in the reference
        """
        PdfObjectProperties.__init__(self, obj, address, idnum)
        self.non_tree_relationships: List[PdfObjectRelationship] = []

        if isinstance(obj, StreamObject):
            try:
                self.stream_data = self.obj.get_data()
                self.stream_length = len(self.stream_data)
            except (NotImplementedError, PdfReadError) as e:
                msg = f"PyPDF2 failed to decode stream in {self}: {e}.\n" + \
                       "Trees will be unaffected but scans/extractions will not be able to check this stream."
                console.print_exception()
                log.warning(msg)
                console.print(msg, style='error')
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
    def find_common_ancestor_among_nodes(cls, nodes: List['PdfTreeNode']) -> Optional['PdfTreeNode']:
        """If any of 'nodes' is a common ancestor of the rest of the 'nodes', return it."""
        for possible_ancestor in nodes:
            log.debug(f"  Checking possible common ancestor: {possible_ancestor}")
            other_nodes = [n for n in nodes if n != possible_ancestor]
            labels = "\n".join([str(n) for n in other_nodes])
            log.debug(f"    Other nodes:\n{labels}")  # TODO: this is excessive logging

            # Look for a common ancestor; if there is one choose it as the parent.
            if all(possible_ancestor in node.ancestors for node in other_nodes):
                other_nodes_str = comma_join([str(node) for node in other_nodes])
                log.info(f"{possible_ancestor} is the common ancestor of {other_nodes_str}")
                return possible_ancestor

    def set_parent(self, parent: 'PdfTreeNode') -> None:
        """Set the parent of this node."""
        if self.parent is not None and self.parent != parent:
            raise PdfWalkError(f"Cannot set {parent} as parent of {self}, parent is already {self.parent}")

        self.parent = parent
        self.remove_non_tree_relationship(parent)
        self.known_to_parent_as = self.address_in_other_node(parent) or self.first_address
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
        child.remove_non_tree_relationship(self)
        child.known_to_parent_as = child.address_in_other_node(self) or child.first_address
        log.info(f"  Added {child} as child of {self}")

    def add_non_tree_relationship(self, relationship: PdfObjectRelationship) -> None:
        """Add a relationship that points at this node's PDF object. TODO: doesn't include parent/child"""
        if relationship in self.non_tree_relationships:
            log.debug(f"{relationship} already in {self}'s other relationships")
            return

        log.info(f'Adding other relationship: {relationship} pointing to {self}')
        self.non_tree_relationships.append(relationship)

    def remove_non_tree_relationship(self, from_node: 'PdfTreeNode') -> None:
        """Remove all non_tree_relationships from from_node to this node"""
        relationships_to_remove = [r for r in self.non_tree_relationships if r.from_node == from_node]

        if len(relationships_to_remove) == 0:
            return
        elif len(relationships_to_remove) > 1 and not all(r.reference_key in [FIRST, LAST] for r in relationships_to_remove):
            log.warning(f"> 1 relationships to remove from {from_node} to {self}: {relationships_to_remove}")

        for relationship in relationships_to_remove:
            log.debug(f"Removing relationship {relationship} from {self}")
            self.non_tree_relationships.remove(relationship)

    def common_ancestor_among_non_tree_relationships(self) -> Optional['PdfTreeNode']:
        """Return the node in non_tree_relationships that is a common ancestor of the other non_tree_relationships"""
        return type(self).find_common_ancestor_among_nodes(self.nodes_with_non_tree_references_to_self())

    # TODO: does not include parent relationships...
    def nodes_with_non_tree_references_to_self(self) -> List['PdfTreeNode']:
        return [r.from_node for r in self.non_tree_relationships if r.from_node]

    def non_tree_relationship_count(self) -> int:
        return len(self.non_tree_relationships)

    def unique_addresses(self) -> List[str]:
        """All the addresses in other nodes that refer to this object."""
        addresses = set([r.address for r in self.non_tree_relationships])

        if self.known_to_parent_as is not None:
            addresses.add(self.known_to_parent_as)

        return list(addresses)

    def unique_labels_of_non_tree_referencers(self) -> Set[str]:
        """Unique labels of nodes related to this one"""
        return set([r.from_node.label for r in self.non_tree_relationships])

    def references_to_other_nodes(self) -> List[PdfObjectRelationship]:
        """Returns all nodes referenced from node.obj (see PdfObjectRelationship definition)"""
        return PdfObjectRelationship.get_references(from_node=self)

    def contains_stream(self) -> bool:
        """Returns True for ContentStream, DecodedStream, and EncodedStream objects"""
        return isinstance(self.obj, StreamObject)

    def tree_address(self, max_length: Optional[int] = DEFAULT_MAX_ADDRESS_LENGTH) -> str:
        """Creates a string like '/Catalog/Pages/Resources[2]/Font' truncated to max_length (if given)"""
        if self.label == TRAILER:
            return '/'
        elif self.parent is None:
            raise PdfWalkError(f"{self} does not have a parent; cannot get accurate node address.")
        elif self.parent.label == TRAILER:
            return self.known_to_parent_as

        address = self.parent.tree_address() + self.known_to_parent_as

        if max_length is None or max_length > len(address):
            return address

        return '...' + address[-max_length:][3:]

    def address_in_other_node(self, from_node: 'PdfTreeNode') -> Optional[str]:
        """Find the local address used in from_node to refer to this node"""
        refs_to_this_node = [ref for ref in from_node.references_to_other_nodes() if ref.to_obj.idnum == self.idnum]

        if len(refs_to_this_node) == 1:
            return refs_to_this_node[0].address
        elif len(refs_to_this_node) == 0:
            # TODO: Hack city. /XRef streams are basically trailer nodes without any direct reference
            if self.parent and self.parent.label == TRAILER and self.type == XREF and XREF_STREAM in self.parent.obj:
                return XREF_STREAM
            elif self.label not in NON_STANDARD_ADDRESS_NODES:
                log.info(f"Could not find expected reference from {from_node} to {self}")

            return None
        else:
            address = refs_to_this_node[0].address

            # Check if other node's label starts with a NON_STANDARD_ADDRESS string
            #    or ALL the relationships in other nodes that point at this one always use a
            #       NON_STANDARD_ADDRESS_NODES string to refer to it.
            #
            # If those things are not true, print a warning.
            if not (is_prefixed_by_any(from_node.label, NON_STANDARD_ADDRESS_NODES) or \
                        all(ref.address in NON_STANDARD_ADDRESS_NODES for ref in refs_to_this_node)):
                refs_to_this_node_str = comma_join([str(r) for r in refs_to_this_node])
                msg = f"Multiple refs from {from_node} to {self}: {refs_to_this_node_str}"
                log.warning(msg + f", using {address}")

            return address

    def print_non_tree_relationships(self) -> None:
        """console.print this node's non tree relationships (represented by SymlinkNodes in the tree)."""
        self._write_non_tree_relationships(console.print)

    def log_non_tree_relationships(self) -> None:
        """log this node's non tree relationships (represented by SymlinkNodes in the tree)."""
        self._write_non_tree_relationships(log.info)

    def _write_non_tree_relationships(self, write_method: Callable) -> None:
        """Use write_method() to write self.non_tree_relationships."""
        write_method(f"Other relationships of {escape(str(self))}")

        for r in self.non_tree_relationships:
            write_method(f"  Relationship: {escape(str(r))}")

    def _colored_address(self, max_length: Optional[int] = None) -> Text:
        """Rich text version of tree_address()"""
        text = Text('@', style='bright_white')
        return text.append(self.tree_address(max_length), style='address')

    def __rich__(self) -> Text:
        return PdfObjectProperties.__rich__(self)[:-1] + self._colored_address() + Text('>')

    def __str__(self) -> str:
        return PdfObjectProperties.__rich__(self).plain

    def __repr__(self) -> str:
        return self.__str__()
