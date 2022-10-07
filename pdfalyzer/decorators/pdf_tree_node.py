"""
PDF object decorator - wraps actual PDF objects to make them anytree nodes.
Also adds decorators/generators for Rich text representation.

Child/parent relationships should be set using the add_child()/set_parent()
methods and not set directly. (TODO: this could be done better with anytree
hooks)
"""
from collections import namedtuple
from numbers import Number
from typing import List, Union

from anytree import NodeMixin, SymlinkNode
from PyPDF2.generic import (DictionaryObject, EncodedStreamObject, IndirectObject, NumberObject, PdfObject,
     StreamObject)
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
from yaralyzer.helpers.bytes_helper import clean_byte_string, hex_text
from yaralyzer.helpers.rich_text_helper import size_text
from yaralyzer.output.rich_console import BYTES_NO_DIM, YARALYZER_THEME, console
from yaralyzer.util.logging import log

from yaralyzer.encoding_detection.character_encodings import NEWLINE_BYTE
from pdfalyzer.helpers.pdf_object_helper import PdfObjectRef, get_references, get_symlink_representation
from pdfalyzer.helpers.rich_text_helper import (PDF_ARRAY, TYPE_STYLES, get_label_style,
     get_type_style, get_type_string_style)
from pdfalyzer.helpers.string_helper import pypdf_class_name
from pdfalyzer.util.adobe_strings import (DANGEROUS_PDF_KEYS, FIRST, FONT, LAST, NEXT, TYPE1_FONT, S,
     SUBTYPE, TRAILER, TYPE, UNLABELED, XREF, XREF_STREAM)
from pdfalyzer.util.exceptions import PdfWalkError

STREAM_PREVIEW_LENGTH_IN_TABLE = 500
DEFAULT_MAX_ADDRESS_LENGTH = 90
STREAM = 'Stream'
HEX = 'Hex'
PREVIEW_STYLES = {HEX: BYTES_NO_DIM, STREAM: 'bytes'}

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

        if isinstance(obj, StreamObject):
            self.stream_data = self.obj.get_data()
            self.stream_length = len(self.stream_data)
        else:
            self.stream_data = None
            self.stream_length = 0

        if isinstance(obj, DictionaryObject):
            self.type = obj.get(TYPE) or known_to_parent_as
            self.label = obj.get(TYPE) or known_to_parent_as
            self.sub_type = obj.get(SUBTYPE) or obj.get(S)

            if isinstance(self.type, str):
                self.type = self.type.split('[')[0]
        else:
            self.type = known_to_parent_as.split('[')[0] if isinstance(known_to_parent_as, str) else known_to_parent_as
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

    def add_relationship(self, from_node: 'PdfTreeNode', reference_key: str) -> None:
        """Handles relationships not covered by the tree structure"""
        relationship = Relationship(from_node, reference_key)

        if relationship in self.other_relationships:
            return

        log.info(f'Adding other relationship: {from_node} ref {reference_key} points to {self}')
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

    def get_reference_key_for_relationship(self, from_node: 'PdfTreeNode'):
        """Get the label that links from_node to this one outside of the tree structure"""
        relationship = next((r for r in self.other_relationships if r.from_node == from_node), None)

        if relationship is None:
            raise PdfWalkError(f"Can't find other relationship from {from_node} to {self}")

        return relationship.reference_key

    # TODO: this doesn't include /Parent references
    def referenced_by_keys(self) -> List[str]:
        """All the PDF instruction strings that referred to this object"""
        return [r.reference_key for r in self.other_relationships] + [self.known_to_parent_as]

    def references(self) -> List[PdfObjectRef]:
        """Returns all nodes referenced from this node (see PdfObjectRef definition)"""
        return get_references(self.obj)

    def contains_stream(self) -> bool:
        """Returns True for ContentStream, DecodedStream, and EncodedStream objects"""
        return isinstance(self.obj, StreamObject)

    def _find_address_of_this_node(self, other_node: 'PdfTreeNode') -> str:
        """Find the address used in other_node to refer to this node"""
        refs_to_this_node = [ref for ref in other_node.references() if ref.pdf_obj.idnum == self.idnum]

        if len(refs_to_this_node) == 1:
            return refs_to_this_node[0].reference_address
        elif len(refs_to_this_node) == 0:
            # /XRef streams are basically trailer nodes without any direct reference
            if self.parent.label == TRAILER and self.type == XREF and XREF_STREAM in self.parent.obj:
                return XREF_STREAM
            elif self.label != NEXT:
                log.warning(f"Could not find expected reference from {other_node} to {self}")
                return None
        else:
            reference_address = refs_to_this_node[0].reference_address

            if not all(ref.reference_address in [FIRST, LAST] for ref in refs_to_this_node):
                log.warning(f"Multiple refs from {other_node} to {self}: {refs_to_this_node}. Using {reference_address} as address")

            return reference_address

    ######################################
    # BELOW HERE IS JUST TEXT FORMATTING #
    ######################################

    def print_other_relationships(self) -> None:
        """Print this node's non tree relationships (the ones represented by SymlinkNodes in the tree)"""
        console.print(f"Other relationships of {escape(str(self))}")

        for r in self.other_relationships:
            console.print(f"  Referenced as {escape(str(r.reference_key))} by {escape(str(r.from_node))}")

    def tree_address(self, max_length: Union[int, None]  = None) -> str:
        """Creates a string like '/Catalog/Pages/Resources/Font' truncated to max_length (if given)"""
        if self.label == TRAILER:
            return '/'

        address = ''.join([str(node.known_to_parent_as) for node in self.path if node.label != TRAILER])
        address_length = len(address)

        if max_length is None or max_length > address_length:
            return address

        return '...' + address[-max_length:][3:]

    def colored_address(self, max_length: Union[int, None] = None) -> Text:
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

        for row in self._get_stream_preview_rows():
            row.append(Text(''))
            table.add_row(*row)

        return table

    def _get_stream_preview_rows(self) -> List[List[Text]]:
        """Get rows that preview the stream data"""
        return_rows: List[List[Text]] = []

        if not isinstance(self.obj, StreamObject):
            return return_rows
        if self.stream_data is None or len(self.stream_data) == 0:
            log.warning(self.__rich__().append(' is a stream object but had no stream data'))
            return return_rows

        stream_preview = self.stream_data[:STREAM_PREVIEW_LENGTH_IN_TABLE]
        stream_preview_length = len(stream_preview)

        if isinstance(self.stream_data, bytes):
            stream_preview_hex = hex_text(stream_preview).plain
        else:
            stream_preview_hex = f"N/A (Stream data is type '{type(self.stream_data).__name__}', not bytes)"

        if isinstance(stream_preview, bytes):
            stream_preview_lines = stream_preview.split(NEWLINE_BYTE)
            stream_preview_string = "\n".join([clean_byte_string(line) for line in stream_preview_lines])
        else:
            stream_preview_string = stream_preview

        def add_preview_row(hex_or_stream: str, stream_string: str):
            if stream_preview_length < STREAM_PREVIEW_LENGTH_IN_TABLE:
                row_label = "Data" if hex_or_stream != HEX else ' View'
            else:
                row_label = "Preview" if hex_or_stream != HEX else ' Preview'
                stream_string += '...'

            style = PREVIEW_STYLES[hex_or_stream]
            row_label = f"{hex_or_stream}{row_label}\n  ({stream_preview_length} bytes)"
            return_rows.append([Text(row_label, 'grey'), Text(stream_string, style)])

        add_preview_row(STREAM, stream_preview_string)
        add_preview_row(HEX, stream_preview_hex)
        return_rows.append([Text('StreamLength', style='grey'), size_text(len(self.stream_data))])
        return return_rows

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

    def _node_label(self) -> Text:
        text = Text('<', style='white')
        text.append(f'{self.idnum}', style='bright_white')
        text.append(':', style='white')
        text.append(self.colored_node_label())
        text.append('(', style='white')
        text.append(self.colored_node_type())
        text.append(')', style='white')
        text.append('>')
        return text

    def __rich__(self) -> Text:
        return self._node_label()[:-1] + self.colored_address(max_length=DEFAULT_MAX_ADDRESS_LENGTH) + Text('>')

    def __str__(self) -> str:
        return self._node_label().plain

    def __repr__(self) -> str:
        return self.__str__()


# TODO: This should probably live in pdf_object_helper.py but the use of PdfTreeNode() makes that a circular reference
def resolve_references(reference_key: str, obj: PdfObject):
    """Recursively build the same data structure except IndirectObjects are resolved to nodes"""
    if isinstance(obj, NumberObject):
        return obj.as_numeric()
    elif isinstance(obj, IndirectObject):
        return PdfTreeNode.from_reference(obj, reference_key)
    elif isinstance(obj, list):
        return [resolve_references(reference_key, item) for item in obj]
    elif isinstance(obj, dict):
        return {k: resolve_references(k, v) for k, v in obj.items()}
    else:
        return obj


def to_table_row(reference_key: str, obj: PdfObject, is_single_row_table=False) -> List[Union[Text, str]]:
    """Turns PDF object properties into a formatted 3-tuple for use in Rich tables representing PdfObjects"""
    # 3rd col (AKA type(value)) is redundant if it's something like a TextString or Number node so we set it to ''
    return [
        Text(f"{reference_key}", style='grey' if isinstance(reference_key, int) else ''),
        Text(f"{escape(str(resolve_references(reference_key, obj)))}", style=get_type_style(type(obj))),
        '' if is_single_row_table else Text(pypdf_class_name(obj), style=get_type_string_style(type(obj)))
    ]


def get_node_type_style(obj):
    klass_string = pypdf_class_name(obj)

    if 'Dictionary' in klass_string:
        style = TYPE_STYLES[dict]
    elif 'EncodedStream' in klass_string:
        style = YARALYZER_THEME.styles['bytes']
    elif 'Stream' in klass_string:
        style = YARALYZER_THEME.styles['bytes.title']
    elif 'Text' in klass_string:
        style = YARALYZER_THEME.styles['grey.light']
    elif 'Array' in klass_string:
        style = PDF_ARRAY
    else:
        style = 'bright_yellow'

    return f"{style} italic"
