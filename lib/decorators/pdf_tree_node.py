"""
PDF object decorator - wraps actual PDF objects to make them anytree nodes.
Also adds decorators/generators for rich text representation.

Child/parent relationships should be set using the add_child()/set_parent()
methods and not set directly. (TODO: this could be done better with anytree
hooks)
"""
from collections import namedtuple
from numbers import Number

from anytree import NodeMixin, SymlinkNode
from PyPDF2.generic import DictionaryObject, EncodedStreamObject, IndirectObject, PdfObject
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from lib.util.adobe_strings import (DANGEROUS_PDF_KEYS, FONT, TYPE, NEXT, TYPE1_FONT, S, SUBTYPE, TRAILER, UNLABELED,
     XREF, XREF_STREAM)
from lib.util.exceptions import PdfWalkError
from lib.util.logging import log
from lib.util.pdf_object_helper import PdfObjectRef, get_references, pdf_object_id
from lib.util.string_utils import (NEWLINE_BYTE, clean_byte_string, console, get_label_style, get_node_type_style,
     get_symlink_representation, get_type_style, get_type_string_style, pypdf_class_name)


DEFAULT_MAX_ADDRESS_LENGTH = 90
STREAM_PREVIEW_LENGTH_IN_TABLE = 500

Relationship = namedtuple('Relationship', ['from_node', 'reference_key'])


class PdfTreeNode(NodeMixin):
    def __init__(self, obj: PdfObject, known_to_parent_as: str, idnum: int):
        """
        reference_key: PDF instruction string used to reference obj
        idnum: ID used in the reference
        """
        self.obj = obj
        self.idnum = idnum
        self.known_to_parent_as = known_to_parent_as
        self.other_relationships = []
        self.all_references_processed = False

        if isinstance(obj, DictionaryObject):
            self.type = obj.get(TYPE)
            self.label = self.type or known_to_parent_as
            self.sub_type = obj.get(SUBTYPE) or obj.get(S)
        else:
            self.type = known_to_parent_as.split('[')[0]
            self.label = known_to_parent_as
            self.sub_type = None

        if isinstance(self.known_to_parent_as, int):
            self.known_to_parent_as = f"[{known_to_parent_as}]"

        if isinstance(self.label, int):
            self.label = f"{UNLABELED}[{self.label}]"

    @classmethod
    def from_reference(cls, ref: IndirectObject, known_to_parent_as: str) -> 'PdfTreeNode':
        """Builds a PdfTreeDecorator from an IndirectObject"""
        return cls(ref.get_object(), known_to_parent_as, ref.idnum)

    def set_parent(self, parent: 'PdfTreeNode') -> None:
        """Set the parent of this node"""
        if self.parent and self.parent != parent:
            raise PdfWalkError(f"Cannot set {parent} as parent of {self}, parent is already {self.parent}")

        self.parent = parent
        # Adjust incorrect known_to_parent_as that can arise when adding non tree references to the walker
        self.known_to_parent_as = self._find_reference_to_this_node(parent)
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

        self.children = self.children + (child,)
        # Adjust incorrect known_to_parent_as that can arise when adding non tree references to the walker
        child.known_to_parent_as = child._find_reference_to_this_node(self)
        log.info(f"  Added {child} as child of {self}")

    def add_relationship(self, from_node: 'PdfTreeNode', reference_key: str) -> None:
        """Handles relationships not covered by the tree structure"""
        relationship = Relationship(from_node, reference_key)

        if relationship in self.other_relationships:
            return

        log.info(f'Adding other relationship: {from_node} ref {reference_key} points to {self}')
        self.other_relationships.append(relationship)

    def other_relationnship_count(self):
        return len(self.other_relationships)

    def get_reference_key_for_relationship(self, from_node: 'PdfTreeNode'):
        """Get the label that links from_node to this one outside of the tree structure"""
        relationship = next((r for r in self.other_relationships if r.from_node == from_node), None)

        if relationship is None:
            raise PdfWalkError(f"Can't find other relationship from {from_node} to {self}")

        return relationship.reference_key

    def referenced_by_keys(self) -> list[str]:
        """All the PDF instruction strings that referred to this object"""
        return [r.reference_key for r in self.other_relationships] + [self.known_to_parent_as]

    def properties(self) -> dict:
        """Does not return references, only stuff like /Type, /Size, etc."""
        return {k: v for (k, v) in self.obj.items() if not isinstance(v, IndirectObject)}

    def references(self):
        return get_references(self.obj)

    def _find_reference_to_this_node(self, other_node: 'PdfTreeNode') -> str:
        """Find the address used in other_node to refer to this node"""
        refs_to_this_node = [ref for ref in other_node.references() if ref.pdf_obj.idnum == self.idnum]

        if len(refs_to_this_node) == 1:
            return refs_to_this_node[0].reference_address
        elif len(refs_to_this_node) == 0:
            # /XRef streams are basically trailer nodes without any direct reference
            if self.parent.label == TRAILER and self.type == XREF and XREF_STREAM in self.parent.obj:
                return XREF_STREAM
            elif self.label != NEXT:
                raise PdfWalkError(f"Could not find reference from {other_node} to {self}")
        else:
            log.warning(f"Multiple references from {other_node} to {self}: {refs_to_this_node}")
            return refs_to_this_node[0].reference_address
            #raise PdfWalkError(f"Multiple references from {other_node} to {self}: {refs_to_this_node}")

    ######################################
    # BELOW HERE IS JUST TEXT FORMATTING #
    ######################################

    def print_other_relationships(self):
        """Print this node's non tree relationships (the ones represented by SymlinkNodes in the tree)"""
        console.print(f"Other relationships of {escape(str(self))}")

        for r in self.other_relationships:
            console.print(f"  Referenced as {escape(str(r.reference_key))} by {escape(str(r.from_node))}")

    def tree_address(self, max_length=None) -> str:
        """Creates a string like '/Catalog/Pages/Resources/Font' truncated to max_length (if given)"""
        if self.label == TRAILER:
            return '/'

        address = ''.join([str(node.known_to_parent_as) for node in self.path if node.label != TRAILER])
        address_length = len(address)

        if max_length is None or max_length > address_length:
            return address

        return '...' + address[-max_length:][3:]

    def colored_address(self, max_length=None) -> Text:
        """Rich text version of tree_address()"""
        text = Text('@', style='bright_white')
        text.append(self.tree_address(max_length), style='address')
        return text

    def colored_node_label(self) -> Text:
        return Text(self.label[1:], style=f'{get_label_style(self.label)} underline bold')

    def colored_node_type(self) -> Text:
        return Text(pypdf_class_name(self.obj), style=get_node_type_style(self.obj))

    def generate_rich_table(self) -> Table:
        """
        Generate a Rich table representation of this node's PDF object and its properties.
        Table cols are [title, address, class name] (not exactly headers but sort of).
        """
        title = f"{self.idnum}.{escape(self.label)}"
        table = Table(title, escape(self.tree_address()), pypdf_class_name(self.obj))
        table.columns[0].header_style = f'reverse {get_label_style(self.label)}'
        table.columns[1].header_style = 'dim'
        table.columns[1].overflow = 'fold'
        table.columns[2].header_style = get_node_type_style(self.obj)

        if self.label != self.known_to_parent_as:
            table.add_row(Text('ParentRefKey', style='grey'), Text(str(self.known_to_parent_as), style='grey'), '')

        if isinstance(self.obj, dict):
            for k, v in self.obj.items():
                row = to_table_row(k, v)

                # Make dangerous stuff look dangerous
                if (k in DANGEROUS_PDF_KEYS) or (self.label == FONT and k == SUBTYPE and v == TYPE1_FONT):
                    table.add_row(*[col.plain for col in row], style='fail')
                else:
                    table.add_row(*row)
        elif isinstance(self.obj, list):
            for i, item in enumerate(self.obj):
                table.add_row(*to_table_row(i, item))
        elif not isinstance(self.obj, EncodedStreamObject):
            # Then it's a single element node like a URI, TextString, etc.
            table.add_row(*to_table_row('', self.obj, is_single_row_table=True))

        # PDF objects can have properties and streams at the same time
        if isinstance(self.obj, EncodedStreamObject):
            # TODO: Add a DataStreamHandler to all nodes with streams instead of using self.obj.get_data()
            stream_data = self.obj.get_data()
            stream_preview = stream_data[:STREAM_PREVIEW_LENGTH_IN_TABLE]
            stream_preview_length = len(stream_preview)

            if isinstance(stream_preview, bytes):
                stream_preview_lines = stream_preview.split(NEWLINE_BYTE)
                stream_preview_string = "\n".join([clean_byte_string(line) for line in stream_preview_lines])
            else:
                stream_preview_string = stream_preview

            table.add_row(
                Text('StreamLength', style='grey'),
                Text(f"{len(stream_data)} bytes", style=get_type_style(Number)),
                Text(f''))

            if stream_preview_length < STREAM_PREVIEW_LENGTH_IN_TABLE:
                preview_row_label = f"StreamData\n  ({stream_preview_length} bytes)"
            else:
                preview_row_label = f"StreamPreview\n  ({STREAM_PREVIEW_LENGTH_IN_TABLE} bytes)"
                stream_preview_string += '...'


            table.add_row(
                Text(preview_row_label, style='grey'),
                Text(stream_preview_string, style='bytes'),
                Text(''))

        return table

    def generate_rich_tree(self, tree=None, depth=0):
        """Recursively generates a rich.tree.Tree object from this node"""
        tree = tree or Tree(self.generate_rich_table())

        for child in self.children:
            if isinstance(child, SymlinkNode):
                symlink_rep = get_symlink_representation(self, child)
                tree.add(Panel(symlink_rep.text, style=symlink_rep.style, expand=False))
                continue

            child_branch = tree.add(child.generate_rich_table())
            child.generate_rich_tree(child_branch)

        return tree

    def _rich_text(self) -> Text:
        text = Text('<', style='white')
        text.append(f'{self.idnum}', style='bright_white')
        text.append(':', style='white')
        text.append(self.colored_node_label())
        text.append('(', style='white')
        text.append(self.colored_node_type())
        text.append(')', style='white')
        text.append('>')
        return text

    def __str_with_color__(self) -> Text:
        return self._rich_text()[:-1] + self.colored_address(max_length=DEFAULT_MAX_ADDRESS_LENGTH) + Text('>')

    def __str__(self) -> str:
        return self._rich_text().plain

    def __repr__(self) -> str:
        return self.__str__()


def to_table_row(reference_key, obj, is_single_row_table=False) -> [Text]:
    """Turns PDF object properties into a formatted 3-tuple for use in Rich tables representing PdfObjects"""
    value_style = get_type_style(type(obj))
    type_string = pypdf_class_name(obj)
    # Type col is redundant if it's something like a TextString node
    type_col_value = '' if is_single_row_table else Text(type_string, style=get_type_string_style(type(obj)))

    if isinstance(reference_key, int):
        reference_col = Text(f"[{reference_key}]", style='grey')
    else:
        reference_col = Text(reference_key)

    if isinstance(obj, Number):
        value = f"{obj.as_numeric()}"
    elif isinstance(obj, IndirectObject):
        value = f"{PdfTreeNode.from_reference(obj, reference_col.plain)}"
    elif isinstance(obj, list):
        value = [
            f"{PdfTreeNode.from_reference(item, reference_col.plain)}" if isinstance(item, IndirectObject) else item
            for item in obj
        ]
    elif isinstance(obj, dict):
        value = {
            k: f"{PdfTreeNode.from_reference(v, k)}" if isinstance(v, IndirectObject) else v
            for k, v in obj.items()
        }
    else:
        value = str(obj)

    return [reference_col, Text(f"{escape(str(value))}", style=value_style), type_col_value]
