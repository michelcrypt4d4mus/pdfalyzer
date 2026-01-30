"""
`PdfTreeNode` decorates a `PdfObject` with tree structure information.
"""
from dataclasses import dataclass, field
from typing import Callable, Self

from anytree import NodeMixin, SymlinkNode
from pypdf.errors import PdfReadError
from pypdf.generic import ArrayObject, IndirectObject, PdfObject, StreamObject
from rich.markup import escape
from rich.table import Table
from rich.text import Text
from yaralyzer.output.console import console
from yaralyzer.output.theme import GREY_ADDRESS
from yaralyzer.util.helpers.env_helper import log_console
from yaralyzer.util.helpers.rich_helper import DEFAULT_TABLE_OPTIONS

from pdfalyzer.decorators.pdf_object_properties import PdfObjectProperties
from pdfalyzer.output.tables.pdf_node_rich_table import get_stream_preview_rows
from pdfalyzer.output.theme import get_class_style_italic
from pdfalyzer.pdf_object_relationship import PdfObjectRelationship
from pdfalyzer.util.adobe_strings import *
from pdfalyzer.util.exceptions import PdfWalkError
from pdfalyzer.util.helpers.pdf_object_helper import pypdf_class_name
from pdfalyzer.util.helpers.string_helper import is_prefixed_by_any, numbered_list
from pdfalyzer.util.logging import log

DEFAULT_MAX_ADDRESS_LENGTH = 90
DECODE_FAILURE_LEN = -1
MAX_REFS_TO_WARN = 10

SORT_KEYS = {
    TYPE: '/A',
    SUBTYPE: '/AA',
    NAME: '/AAA',
    TITLE: '/AAAA',
}


@dataclass
class PdfTreeNode(NodeMixin):
    """
    PDF node decorator - wraps actual PDF objects to make them `anytree` nodes.
    Also adds decorators/generators for Rich text representation.

    Child/parent relationships should be set using the `add_child()` and `set_parent()`
    methods and not set directly.
    TODO: this could be done better with anytree hooks.
    """
    pdf_object: PdfObjectProperties

    # Computed fields
    all_references_processed: bool = False
    known_to_parent_as: str | None = None
    non_tree_relationships: list[PdfObjectRelationship] = field(default_factory=list)
    stream_data: bytes | None = None
    stream_length: int = 0

    @property
    def idnum(self) -> int:
        return self.pdf_object.idnum

    @property
    def label(self) -> str:
        return self.pdf_object.label

    @property
    def obj(self) -> PdfObject:
        return self.pdf_object.obj

    @property
    def type(self) -> str | None:
        return self.pdf_object.type

    def __post_init__(self):
        if self.contains_stream():
            try:
                self.stream_data = self.obj.get_data()
                self.stream_length = len(self.stream_data)
            except (NotImplementedError, PdfReadError) as e:
                log_console.print_exception()
                msg = f"Failed to decode stream in {self}, won't be able to scan/check this stream: {e}"
                log.error(msg)
                self.stream_data = msg.encode()
                self.stream_length = DECODE_FAILURE_LEN

    @classmethod
    def from_reference(cls, ref: IndirectObject, address: str) -> Self:
        """Alternate constructor to Build a `PdfTreeNode` from an `IndirectObject`."""
        return cls(PdfObjectProperties.from_reference(ref, address))

    @classmethod
    def from_obj(cls, obj: PdfObject, address: str, idnum: int) -> Self:
        """Alternate constructor to Build a `PdfTreeNode` from an `IndirectObject`."""
        return cls(PdfObjectProperties(obj, address, idnum))

    def set_parent(self, parent: Self | None, force: bool = False) -> None:
        """Set the parent of this node."""
        if parent is None:
            return
        elif self.parent is not None and self.parent != parent and not force:
            # Some objs in Arrays have the array's parent in /Parent so we link through
            if isinstance(self.parent.obj, ArrayObject):
                log.warning(f"Parent of {self} is already {self.parent} but it's an array; inserting {parent} as grandparent")  # noqa: E501
                parent.set_parent(self.parent)
                self.parent = parent
            else:
                log.warning(f"Cannot set {parent} as parent of {self}, parent is already {self.parent}")

            return

        self.parent = parent
        self.remove_non_tree_relationship(parent)
        self.known_to_parent_as = self.address_of_this_node_in_other(parent) or self.pdf_object.address
        log.info(f"  Added {parent} as parent of {self}" + (' by force' if force else ''))

    def add_child(self, child: Self) -> None:
        """Add a child to this node."""
        if next((c for c in self.children if c.idnum == child.idnum), None) is not None:
            log.debug(f"{child} is already child of {self}")
        else:
            child.set_parent(self)

    def add_non_tree_relationship(self, relationship: PdfObjectRelationship) -> None:
        """Add a relationship that points at this node's PDF object. TODO: doesn't include parent/child."""
        if relationship in self.non_tree_relationships:
            return

        self.non_tree_relationships.append(relationship)
        log.info(f'Added other relationship: {relationship} {self}')

    def remove_non_tree_relationship(self, from_node: Self) -> None:
        """Remove all non_tree_relationships from 'from_node' to this node."""
        relationships_to_remove = [r for r in self.non_tree_relationships if r.from_node == from_node]
        num_to_remove = len(relationships_to_remove)

        if num_to_remove > 1 and not all(r.reference_key in [FIRST, LAST] for r in relationships_to_remove):
            log.warning(f"Removing {num_to_remove} non-tree relationships between {from_node} and {self}.\n"
                        + numbered_list(relationships_to_remove))

        for relationship in relationships_to_remove:
            log.debug(f"Removing relationship {relationship} from {self}")
            self.non_tree_relationships.remove(relationship)

    def nodes_with_here_references(self) -> list[Self]:
        """Return a list of nodes that contain this node's PDF object as an IndirectObject reference."""
        return [r.from_node for r in self.non_tree_relationships if r.from_node]

    def non_tree_relationship_count(self) -> int:
        """Number of non parent/child relationships containing this node."""
        return len(self.non_tree_relationships)

    def unique_addresses(self) -> list[str]:
        """All the addresses in other nodes that refer to this object."""
        addresses = set([r.address for r in self.non_tree_relationships])

        if self.known_to_parent_as is not None:
            addresses.add(self.known_to_parent_as)

        return list(addresses)

    def references_to_other_nodes(self) -> list[PdfObjectRelationship]:
        """Returns all nodes referenced from node.obj (see PdfObjectRelationship definition)."""
        return PdfObjectRelationship.build_node_references(from_node=self)

    def contains_stream(self) -> bool:
        """Returns True for ContentStream, DecodedStream, and EncodedStream objects."""
        return isinstance(self.obj, StreamObject)

    def tree_address(self, max_length: int = DEFAULT_MAX_ADDRESS_LENGTH) -> str:
        """Creates a string like '/Catalog/Pages/Resources[2]/Font' truncated to max_length (if given)."""
        if self.label == TRAILER:
            return '/'
        elif self.parent is None:
            raise PdfWalkError(f"{self} does not have a parent; cannot get accurate node address.")
        elif self.parent.label == TRAILER:
            return self.known_to_parent_as   # noqa: if there's a parent there's always a known_to_parent_as

        address = self.parent.tree_address() + self.known_to_parent_as

        if max_length is None or max_length > len(address):
            return address

        return '...' + address[-max_length:][3:]

    def address_of_this_node_in_other(self, from_node: Self) -> str | None:
        """Find the local address used in 'from_node' to refer to this node."""
        refs_to_this_node = [
            ref for ref in from_node.references_to_other_nodes()
            if ref.to_obj.idnum == self.idnum
        ]

        if len(refs_to_this_node) == 1:
            return refs_to_this_node[0].address
        elif len(refs_to_this_node) == 0:
            # TODO: Hack city. /XRef streams are basically trailer nodes without any direct reference
            if self.parent and self.parent.label == TRAILER and self.type == XREF and XREF_STREAM in self.parent.obj:
                return XREF_STREAM
            elif self.label not in NON_STANDARD_ADDRESS_NODES:
                log.info(f"Could not find expected reference from {from_node} to {self}")
            else:
                return None
        else:
            address = refs_to_this_node[0].address

            # If other node's label doesn't start with a NON_STANDARD_ADDRESS string
            # AND any of the relationships pointing at this node use something other than a
            #     NON_STANDARD_ADDRESS_NODES string to refer here,
            # then print a warning about multiple refs.
            if not (is_prefixed_by_any(from_node.label, NON_STANDARD_ADDRESS_NODES)
                    or all(ref.address in NON_STANDARD_ADDRESS_NODES for ref in refs_to_this_node)):
                ref_addresses = [r.address for r in refs_to_this_node]
                common_key = next((k for k in MULT_REF_RESOURCE_KEYS if all(k in a for a in ref_addresses)), None)
                msg = f"Found {len(refs_to_this_node)} refs from {from_node} to {self}"
                refs_to_print = refs_to_this_node

                if common_key and len(ref_addresses) > MAX_REFS_TO_WARN:
                    msg += f", they're all {common_key} so showing only first {MAX_REFS_TO_WARN}"
                    refs_to_print = refs_to_this_node[0:MAX_REFS_TO_WARN]

                log.warning(f"{msg}:\n{numbered_list(refs_to_print)}\nCommon address of refs: {address}")

            return address

    def tree_relationships(self) -> list[Self]:
        """Returns parents and children."""
        return list(self.children) + ([self.parent] if self.parent is not None else [])

    def symlink_non_tree_relationships(self) -> None:
        """Create SymlinkNodes for this node's non parent/child (non-tree) relationships."""
        log.info(f"Symlinking {self}'s {self.non_tree_relationship_count()} other relationships...")

        for relationship in self.non_tree_relationships:
            if relationship.from_node in self.tree_relationships():
                log.info(f"{relationship} is non-tree symlink but {relationship.from_node} is now a real "
                         f"parent or child of {self}, removing non-tree relationships")
                self.remove_non_tree_relationship(relationship.from_node)
            else:
                log.debug(f"   SymLinking {relationship} to {self}")
                SymlinkNode(self, parent=relationship.from_node)

    def descendants_count(self) -> int:
        """Count nodes in the tree that are children/grandchildren/great grandchildren/etc of this one."""
        return len(self.children) + sum([child.descendants_count() for child in self.children])

    def unique_labels_of_referring_nodes(self) -> list[str]:
        """Unique label strings of nodes referring here outside the parent/child hierarchy."""
        return list(set([r.from_node.label for r in self.non_tree_relationships]))

    def print_non_tree_relationships(self) -> None:
        """console.print this node's non tree relationships (represented by SymlinkNodes in the tree)."""
        self._write_non_tree_relationships(console.print)

    def log_non_tree_relationships(self) -> None:
        """log this node's non tree relationships (represented by SymlinkNodes in the tree)."""
        self._write_non_tree_relationships(log.info)

    # Presentation
    def as_tree_node_table(self, pdfalyzer: 'Pdfalyzer') -> Table:
        """
        Generate a Rich table representation of this node's PDF object and its properties.
        Table cols are [title, address, class name] (not exactly headers but sort of).
        Dangerous things like /JavaScript, /OpenAction, Type1 fonts, etc, will be highlighted red.

        Args:
            pdfalyzer (Pdfalyzer): Used to lookup nodes with properly assigned types to use in the table
        """
        title = f"{self.idnum}.{escape(self.label)}"
        address = escape(self.tree_address())

        if self.type == OBJ_STM:
            address += ' (should have been decompressed into other objs)'
            table_style = 'dim'
        else:
            table_style = ''

        table = Table(title, address, pypdf_class_name(self.obj), style=table_style, **DEFAULT_TABLE_OPTIONS)
        table.columns[0].header_style = f'reverse {self.pdf_object.label_style}'
        table.columns[1].header_style = 'dim'
        table.columns[1].overflow = 'fold'
        table.columns[2].header_style = get_class_style_italic(self.obj)

        if self.label != self.known_to_parent_as and self.type != TRAILER and self.known_to_parent_as:
            table.add_row(Text('AddressInParent', style='italic'), Text(self.known_to_parent_as), '', style='gray58')

        if isinstance(self.obj, dict):
            for k in sorted(self.obj.keys(), key=lambda k: SORT_KEYS.get(k, k)):
                row = self.pdf_object.get_table_row(k, pdfalyzer)

                # Make dangerous stuff look dangerous
                if (k in DANGEROUS_PDF_KEYS) or (self.label == FONT and k == SUBTYPE and v == TYPE1_FONT):
                    table.add_row(*[col.plain for col in row], style='bold reverse red')
                else:
                    table.add_row(*row)
        elif isinstance(self.obj, list):
            for i in range(len(self.obj)):
                table.add_row(*self.pdf_object.get_table_row(i, pdfalyzer))
        else:
            # Then it's a single element node like a URI, TextString, etc.
            table.add_row(*self.pdf_object.get_table_row(None, pdfalyzer, empty_3rd_col=True))

        for row in get_stream_preview_rows(self):
            table.add_row(*(row + [Text('')]))

        return table

    def _colored_address(self, max_length: int = DEFAULT_MAX_ADDRESS_LENGTH) -> Text:
        """Rich text version of tree_address()."""
        text = Text('@', style='bright_white')
        return text.append(self.tree_address(max_length), style=GREY_ADDRESS)

    def _write_non_tree_relationships(self, write_method: Callable) -> None:
        """Use write_method() to write self.non_tree_relationships."""
        write_method(f"{escape(str(self))} parent from candidates:")

        for i, r in enumerate(self.non_tree_relationships):
            write_method(f"  {i + 1}. {escape(str(r))}, Descendant Count: {r.from_node.descendants_count()}")

    def __repr__(self) -> str:
        return self.__str__()

    def __rich__(self) -> Text:
        """Like the __rich__() of PdfObjectProperties but with address appended."""
        return self.pdf_object.__rich__()[:-1] + self._colored_address() + Text('>')

    def __str__(self) -> str:
        return self.pdf_object.__rich__().plain
