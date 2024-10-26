"""
Walks the PDF objects and builds the PDF logical structure tree by
wrapping each internal PDF object in a PdfTreeNode. Tree is managed by
the anytree library. Information about the tree as a whole is stored
in this class.
Once the PDF is parsed this class manages access to
information about or from the underlying PDF tree.
"""
from os.path import basename
from typing import Dict, Iterator, List, Optional

from anytree import LevelOrderIter, SymlinkNode
from anytree.search import findall, findall_by_attr
from pypdf import PdfReader
from pypdf.generic import IndirectObject
from yaralyzer.helpers.file_helper import load_binary_data
from yaralyzer.output.file_hashes_table import compute_file_hashes
from yaralyzer.output.rich_console import console
from yaralyzer.util.logging import log

from pdfalyzer.decorators.document_model_printer import print_with_header
from pdfalyzer.decorators.indeterminate_node import IndeterminateNode
from pdfalyzer.decorators.pdf_tree_node import PdfTreeNode
from pdfalyzer.decorators.pdf_tree_verifier import PdfTreeVerifier
from pdfalyzer.font_info import FontInfo
from pdfalyzer.pdf_object_relationship import PdfObjectRelationship
from pdfalyzer.util.adobe_strings import *
from pdfalyzer.util.exceptions import PdfWalkError

TRAILER_FALLBACK_ID = 10000000


class Pdfalyzer:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_basename = basename(pdf_path)
        self.pdf_bytes = load_binary_data(pdf_path)
        self.pdf_bytes_info = compute_file_hashes(self.pdf_bytes)
        pdf_file = open(pdf_path, 'rb')  # Filehandle must be left open for PyPDF to perform seeks
        self.pdf_reader = PdfReader(pdf_file)

        # Initialize tracking variables
        self.indeterminate_ids = set()  # See INDETERMINATE_REF_KEYS comment
        self.nodes_encountered: Dict[int, PdfTreeNode] = {}  # Nodes we've seen already
        self.font_infos: List[FontInfo] = []  # Font summary objects
        self.max_generation = 0  # PDF revisions are "generations"; this is the max generation encountered

        # Bootstrap the root of the tree with the trailer. PDFs are always read trailer first.
        # Technically the trailer has no PDF Object ID but we set it to the /Size of the PDF.
        trailer = self.pdf_reader.trailer
        self.pdf_size = trailer.get(SIZE)
        trailer_id = self.pdf_size if self.pdf_size is not None else TRAILER_FALLBACK_ID
        self.pdf_tree = PdfTreeNode(trailer, TRAILER, trailer_id)
        self.nodes_encountered[self.pdf_tree.idnum] = self.pdf_tree

        # Build tree by recursively following relationships between nodes
        self.walk_node(self.pdf_tree)

        # After scanning all objects we place nodes whose position was uncertain, extract fonts, and verify
        self._resolve_indeterminate_nodes()
        self._extract_font_infos()
        self.verifier = PdfTreeVerifier(self)
        self.verifier.verify_all_nodes_encountered_are_in_tree()
        self.verifier.verify_unencountered_are_untraversable()

        # Create SymlinkNodes for relationships between PDF objects that are not parent/child relationships.
        # (Do this last because it has the side effect of making a lot more nodes)
        for node in self.node_iterator():
            if not isinstance(node, SymlinkNode):
                node.symlink_non_tree_relationships()

        log.info(f"Walk complete.")

    def walk_node(self, node: PdfTreeNode) -> None:
        """Recursively walk the PDF's tree structure starting at a given node"""
        log.info(f'walk_node() called with {node}. Object dump:\n{print_with_header(node.obj, node.label)}')
        nodes_to_walk_next = [self._add_relationship_to_pdf_tree(r) for r in node.references_to_other_nodes()]
        node.all_references_processed = True

        for next_node in [n for n in nodes_to_walk_next if not (n is None or n.all_references_processed) ]:
            if not next_node.all_references_processed:
                self.walk_node(next_node)

    def find_node_by_idnum(self, idnum) -> Optional[PdfTreeNode]:
        """Find node with idnum in the tree. Return None if that node is not reachable from the root."""
        nodes = [
            node for node in findall_by_attr(self.pdf_tree, name='idnum', value=idnum)
            if not isinstance(node, SymlinkNode)
        ]

        if len(nodes) == 0:
            return None
        elif len(nodes) == 1:
            return nodes[0]
        else:
            raise PdfWalkError(f"Too many nodes had id {idnum}: {nodes}")

    def is_in_tree(self, search_for_node: PdfTreeNode) -> bool:
        """Returns true if search_for_node is in the tree already."""
        return any([node == search_for_node for node in self.node_iterator()])

    def node_iterator(self) -> Iterator[PdfTreeNode]:
        """Iterate over nodes, grouping them by distance from the root."""
        return LevelOrderIter(self.pdf_tree)

    def stream_nodes(self) -> List[PdfTreeNode]:
        """List of actual nodes (not SymlinkNodes) containing streams sorted by PDF object ID"""
        stream_filter = lambda node: node.contains_stream() and not isinstance(node, SymlinkNode)
        return sorted(findall(self.pdf_tree, stream_filter), key=lambda r: r.idnum)

    def _add_relationship_to_pdf_tree(self, relationship: PdfObjectRelationship) -> Optional[PdfTreeNode]:
        """
        Place the relationship 'node' in the tree. Returns an optional node that should be
        placed in the PDF node processing queue.
        """
        log.info(f'Assessing relationship {relationship}...')
        was_seen_before = (relationship.to_obj.idnum in self.nodes_encountered) # Must come before _build_or_find()
        from_node = relationship.from_node
        to_node = self._build_or_find_node(relationship.to_obj, relationship.address)
        self.max_generation = max([self.max_generation, relationship.to_obj.generation or 0])

        # If one is already a parent/child of the other there's nothing to do
        if to_node == from_node.parent or to_node in from_node.children:
            log.debug(f"  {from_node} and {to_node} are already related")
            return None

        # Many branches return None or don't return.
        # If there's an explicit /Parent or /Kids relationship then we know the correct relationship
        if relationship.is_parent or relationship.is_child:
            log.debug(f"  Explicit parent/child link: {relationship}")

            if relationship.is_parent:
                from_node.set_parent(to_node)
            elif to_node.parent is not None:
                # Some StructElem nodes I have seen use /P or /K despire not being the real parent/child
                if relationship.from_node.type.startswith(STRUCT_ELEM):# reference_key != relationship.address:
                    log.info(f"{relationship} fail: {to_node} parent is already {to_node.parent}")
                else:
                    log.warning(f"{relationship} fail: {to_node} parent is already {to_node.parent}")
            else:
                from_node.add_child(to_node)

            # Remove this to_node from inteterminacy now that it's got a child or parent
            if relationship.to_obj.idnum in self.indeterminate_ids:
                log.info(f"  Found {relationship} => {to_node} was marked indeterminate but now placed")
                self.indeterminate_ids.remove(relationship.to_obj.idnum)

        # If the relationship is indeterminate or we've seen the PDF object before, add it as
        # a non-tree relationship for now. An attempt to place the node will be made at the end.
        elif relationship.is_indeterminate or relationship.is_link or was_seen_before:
            to_node.add_non_tree_relationship(relationship)

            # If we already encountered 'to_node' then skip adding it to the queue of nodes to walk
            if was_seen_before:
                if relationship.to_obj.idnum not in self.indeterminate_ids and to_node.parent is None:
                    raise PdfWalkError(f"{relationship} - ref has no parent and is not indeterminate")
                else:
                    log.debug(f"  Already saw {relationship}; not scanning next")
                    return None
            # Indeterminate relationships need to wait until everything has been scanned to be placed
            elif relationship.is_indeterminate or (relationship.is_link and not self.is_in_tree(to_node)):
                log.info(f'  Indeterminate ref {relationship}')
                self.indeterminate_ids.add(to_node.idnum)
            # Link nodes like /Dest are usually just links between nodes
            elif relationship.is_link:
                log.debug(f"  Link ref {relationship}")

        # If no other conditions are met make from_node the parent of to_node
        else:
            from_node.add_child(to_node)

        return to_node

    def _resolve_indeterminate_nodes(self) -> None:
        """Place all indeterminate nodes in the tree."""
        #set_log_level('INFO')
        indeterminate_nodes = [self.nodes_encountered[idnum] for idnum in self.indeterminate_ids]
        indeterminate_nodes_string = "\n   ".join([f"{node}" for node in indeterminate_nodes])
        log.info(f"Resolving {len(indeterminate_nodes)} indeterminate nodes: {indeterminate_nodes_string}")

        for node in indeterminate_nodes:
            if node.parent is not None:
                log.info(f"{node} marked indeterminate but has parent: {node.parent}")
                continue

            IndeterminateNode(node).place_node()

    def _extract_font_infos(self) -> None:
        """Extract information about fonts in the tree and place it in self.font_infos"""
        for node in self.node_iterator():
            if isinstance(node.obj, dict) and RESOURCES in node.obj:
                log.debug(f"Extracting fonts from node with '{RESOURCES}' key: {node}...")
                known_font_ids = [fi.idnum for fi in self.font_infos]

                self.font_infos += [
                    fi for fi in FontInfo.extract_font_infos(node.obj)
                    if fi.idnum not in known_font_ids
                ]

    def _build_or_find_node(self, relationship: IndirectObject, relationship_key: str) -> PdfTreeNode:
        """If node in self.nodes_encountered already then return it, otherwise build a node and store it."""
        if relationship.idnum in self.nodes_encountered:
            return self.nodes_encountered[relationship.idnum]

        log.debug(f"Building node for {relationship}")
        new_node = PdfTreeNode.from_reference(relationship, relationship_key)
        self.nodes_encountered[relationship.idnum] = new_node
        return new_node

    def _print_nodes_encountered(self) -> None:
        """Debug method that displays which nodes have already been walked"""
        for i in sorted(self.nodes_encountered.keys()):
            console.print(f'{i}: {self.nodes_encountered[i]}')
