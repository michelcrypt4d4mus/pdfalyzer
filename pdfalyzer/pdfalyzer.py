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
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
from PyPDF2.generic import IndirectObject, NameObject, NumberObject
from rich.markup import escape
from yaralyzer.helpers.bytes_helper import get_bytes_info
from yaralyzer.helpers.file_helper import load_binary_data
from yaralyzer.output.rich_console import console
from yaralyzer.util.logging import log, set_log_level

from pdfalyzer.decorators.document_model_printer import print_with_header
from pdfalyzer.decorators.pdf_tree_node import PdfTreeNode, find_node_with_most_descendants
from pdfalyzer.font_info import FontInfo
from pdfalyzer.helpers.string_helper import all_strings_are_same_ignoring_numbers, has_a_common_substring
from pdfalyzer.pdf_object_relationship import PdfObjectRelationship
from pdfalyzer.util.adobe_strings import *
from pdfalyzer.util.exceptions import PdfWalkError

TRAILER_FALLBACK_ID = 10000000


class Pdfalyzer:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_basename = basename(pdf_path)
        self.pdf_bytes = load_binary_data(pdf_path)
        self.pdf_bytes_info = get_bytes_info(self.pdf_bytes)
        pdf_file = open(pdf_path, 'rb')  # Filehandle must be left open for PyPDF2 to perform seeks
        self.pdf_reader = PdfReader(pdf_file)

        # Initialize tracking variables
        self.indeterminate_ids = set()  # See INDETERMINATE_REF_KEYS comment
        self.nodes_encountered: Dict[int, PdfTreeNode] = {}  # Nodes we've seen already
        self.font_infos: List[FontInfo] = []  # Font summary objects
        self.max_generation = 0  # PDF revisions are "generations"; this is the max generation encountered

        # Bootstrap the root of the tree with the trailer. PDFs are always read trailer first.
        # Extract trailer. Technically the trailer has no PDF obj. ID but we set it to the /Size of the PDF
        trailer = self.pdf_reader.trailer
        self.pdf_size = trailer.get(SIZE)
        trailer_id = self.pdf_size if self.pdf_size is not None else TRAILER_FALLBACK_ID
        self.pdf_tree = PdfTreeNode(trailer, TRAILER, trailer_id)
        self.nodes_encountered[self.pdf_tree.idnum] = self.pdf_tree
        self.walk_node(self.pdf_tree)  # Build tree by recursively following relationships between nodes

        # After scanning all objects we place nodes whose position was uncertain, extract fonts, and verify
        self._resolve_indeterminate_nodes()
        self._extract_font_infos()
        self._verify_all_nodes_encountered_are_in_tree()
        self._verify_unencountered_are_untraversable()

        # Create SymlinkNodes for relationships between PDF objects that are not parent/child relationships.
        # (Do this last because it has the side effect of making a lot more nodes)
        for node in self.node_iterator():
            if not isinstance(node, SymlinkNode):
                node.symlink_non_tree_relationships()

        log.info(f"Walk complete.")

    def walk_node(self, node: PdfTreeNode) -> None:
        """Recursively walk the PDF's tree structure starting at a given node"""
        log.info(f'walk_node() called with {node}. Object dump:\n{print_with_header(node.obj, node.label)}')
        nodes_to_walk_next = [self._process_relationship(r) for r in node.references_to_other_nodes()]
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

    def stream_nodes(self) -> List[PdfTreeNode]:
        """List of actual nodes (not SymlinkNodes) containing streams sorted by PDF object ID"""
        stream_filter = lambda node: node.contains_stream() and not isinstance(node, SymlinkNode)
        return sorted(findall(self.pdf_tree, stream_filter), key=lambda r: r.idnum)

    def is_in_tree(self, search_for_node: PdfTreeNode) -> bool:
        """Returns true if search_for_node is in the tree already."""
        for node in self.node_iterator():
            if node == search_for_node:
                return True

        return False

    def node_iterator(self) -> Iterator[PdfTreeNode]:
        """Iterate over nodes, grouping them by distance from the root."""
        return LevelOrderIter(self.pdf_tree)

    def _process_relationship(self, relationship: PdfObjectRelationship) -> Optional[PdfTreeNode]:
        """
        Place the relationship 'node' in the tree. Returns a list of nodes to walk next.
        'address' is the key used in node.obj to refer to 'relationship' object
           plus any modifiers like [2] or [/Something]
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
                if relationship.from_node.type.startswith(STRUCT_ELEM):# reference_key != relationship.address:
                    log.info(f"{relationship} to {to_node} has different key v. address. Not placed; parent is {to_node.parent}")
                else:
                    log.warning(f"{relationship} cound not become parent of {to_node} bc parent is {to_node.parent}")
            else:
                from_node.add_child(to_node)

            # Remove this to_node from inteterminacy now that it's got a child or parent
            if relationship.to_obj.idnum in self.indeterminate_ids:
                log.info(f"  Found {relationship} => {to_node} was marked indeterminate but now placed")
                self.indeterminate_ids.remove(relationship.to_obj.idnum)
        elif relationship.is_indeterminate or relationship.is_link or was_seen_before:
            to_node.add_non_tree_relationship(relationship)

            if was_seen_before:
                if relationship.to_obj.idnum not in self.indeterminate_ids and to_node.parent is None:
                    raise PdfWalkError(f"{relationship} - ref has no parent and is not indeterminate")
                else:
                    log.debug(f"  Already saw {relationship}; not scanning next")
                    return None

            # Indeterminate relationships need to wait until everything has been scanned to be placed
            if relationship.is_indeterminate or (relationship.is_link and not self.is_in_tree(to_node)):
                log.info(f'  Indeterminate ref {relationship}')
                self.indeterminate_ids.add(to_node.idnum)
            elif relationship.is_link:
                log.debug(f"  Link ref {relationship}")  # Link nodes like /Dest are usually just links between nodes
        else:
            # If no other conditions are met, add the relationship as a child
            from_node.add_child(to_node)

        return to_node

    def _resolve_indeterminate_nodes(self) -> None:
        """
        Some nodes cannot be placed until we have walked the rest of the tree. For instance
        if we encounter a /Page that relationships /Resources we need to know if there's a
        /Pages parent of the /Page before committing to a tree structure.
        """
        #set_log_level('INFO')
        indeterminate_nodes = [self.nodes_encountered[idnum] for idnum in self.indeterminate_ids]
        indeterminate_nodes_string = "\n   ".join([f"{node}" for node in indeterminate_nodes])
        log.info(f"Resolving {len(indeterminate_nodes)} indeterminate nodes: {indeterminate_nodes_string}")

        # Looking for situations where we can pick the node with the most descendants that
        # has a relationship to the indeterminate node as the parent
        for node in indeterminate_nodes:
            if node.parent is not None:
                log.info(f"{node} marked indeterminate but has parent: {node.parent}")
                continue
            elif self._attempt_tree_placement(node):
                continue

            log.debug(f"Attempting to resolve indeterminate node: {node}")
            unique_refferer_labels = node.unique_labels_of_referring_nodes()
            unique_addresses = node.unique_addresses()
            possible_parent_relationships = node.non_tree_relationships.copy()

            explicit_tree_relationships = [
                r for r in possible_parent_relationships
                if r.reference_key in [K, KIDS]
            ]

            if len(explicit_tree_relationships) == 1:
                log.info(f"Explicit child relationship: {explicit_tree_relationships[0]}")
                node.set_parent(explicit_tree_relationships[0].from_node)
                continue

            # Note this checks the from_node.type, not the reference key
            page_relationships = [
                r for r in possible_parent_relationships
                if r.from_node.type in PAGE_AND_PAGES
            ]

            if len(page_relationships) == 1:
                log.info(f"Preferentially choosing /Page(s) as parent: {page_relationships[0]}")
                node.set_parent(page_relationships[0].from_node)
                continue

            # Check addresses and referring node labels to see if they are all the same
            reference_keys_or_nodes_are_same = any([
                all_strings_are_same_ignoring_numbers(_list) or has_a_common_substring(_list)
                for _list in [unique_addresses, unique_refferer_labels]
            ])

            possible_parents = [r.from_node for r in possible_parent_relationships]
            parent = find_node_with_most_descendants(possible_parents)

            # Clauses that don't 'raise' or 'continue' result in related node with lowest ID being made parent
            if reference_keys_or_nodes_are_same:
                log.info(f"Fuzzy match addresses: {unique_addresses} / labels: {unique_refferer_labels}")
            elif node.type == COLOR_SPACE:
                log.info("Color space node found; placing at lowest ID")
            else:
                log.warning(f"Indeterminate {node} parent {escape(str(parent))} chosen based on descendant count, not PDF logic.")
                node.log_non_tree_relationships()

            node.set_parent(parent)

    def _attempt_tree_placement(self, node: PdfTreeNode) -> bool:
        """Attempt to find place for node in self.pdf_tree."""
        # As opposed to INDETERMINITE
        determinate_relationships = [
            r for r in node.non_tree_relationships
            if r.from_node.type not in NON_TREE_KEYS
        ]

        common_ancestor_among_possible_parents = node.common_ancestor_among_non_tree_relationships()
        log.info(f"Found {len(determinate_relationships)} determinate relationships...")

        if common_ancestor_among_possible_parents is not None:
            log.info(f"  Found common ancestor: {common_ancestor_among_possible_parents}")
            node.set_parent(common_ancestor_among_possible_parents)
        elif len(determinate_relationships) == 1:
            log.info(f"  Single determinate_relationship {determinate_relationships[0]}; making it the parent")
            node.set_parent(determinate_relationships[0].from_node)
        elif set(node.unique_labels_of_referring_nodes()) == set(PAGE_AND_PAGES):
            # An edge case seen in the wild involving a PDF that doesn't conform to the PDF spec
            log.warning(f"  Failed to place {node}; seems to be a loose {PAGE}. Linking to first {PAGES}")
            pages_nodes = [n for n in node.nodes_with_non_tree_references_to_self() if node.type == PAGES]
            node.set_parent(sorted(pages_nodes, key=lambda n: n.idnum)[0])
        else:
            return False  # Then we didn't manage to place it.

        return True

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
        """If node exists in self.nodes_encountered return it, otherwise build a node and store it."""
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

    def _verify_all_nodes_encountered_are_in_tree(self) -> None:
        """Make sure every node we can see is reachable from the root of the tree"""
        missing_nodes = [
            node for idnum, node in self.nodes_encountered.items()
            if self.find_node_by_idnum(idnum) is None
        ]

        if len(missing_nodes) > 0:
            msg = f"Nodes were traversed but never placed: {escape(str(missing_nodes))}\n" + \
                   "For link nodes like /First, /Next, /Prev, and /Last this might be no big deal - depends " + \
                   "on the PDF. But for other node typtes this could indicate missing data in the tree."
            console.print(msg)
            log.warning(msg)

    def _verify_unencountered_are_untraversable(self) -> None:
        """Make sure any PDF object IDs we can't find in tree are /ObjStm or /Xref nodes"""
        if self.pdf_size is None:
            log.warning(f"{SIZE} not found in PDF trailer; cannot verify all nodes are in tree")
            return
        if self.max_generation > 0:
            log.warning(f"_verify_unencountered_are_untraversable() only checking generation {self.max_generation}")

        # We expect to see all ordinals up to the number of nodes /Trailer claims exist as obj. IDs.
        missing_node_ids = [i for i in range(1, self.pdf_size) if self.find_node_by_idnum(i) is None]

        for idnum in missing_node_ids:
            ref = IndirectObject(idnum, self.max_generation, self.pdf_reader)

            try:
                obj = ref.get_object()
            except PdfReadError as e:
                if 'Invalid Elementary Object' in str(e):
                    log.warning(f"Couldn't verify elementary obj with id {idnum} is properly in tree")
                    continue
                log.error(str(e))
                console.print_exception()
                obj = None
                raise e

            if obj is None:
                log.error(f"Cannot find ref {ref} in PDF!")
                continue
            elif isinstance(obj, (NumberObject, NameObject)):
                log.info(f"Obj {idnum} is a {type(obj)} w/value {obj}; if relationshipd by /Length etc. this is a nonissue but maybe worth doublechecking")
                continue
            elif not isinstance(obj, dict):
                log.error(f"Obj {idnum} ({obj}) of type {type(obj)} isn't dict, cannot determine if it should be in tree")
                continue
            elif TYPE not in obj:
                msg = f"Obj {idnum} has no {TYPE} and is not in tree. Either a loose node w/no data or an error in pdfalyzer."
                msg += f"\nHere's the contents for you to assess:\n{obj}"
                log.warning(msg)
                continue

            obj_type = obj[TYPE]

            if obj_type == OBJECT_STREAM:
                log.debug(f"Object with id {idnum} not found in tree because it's an {OBJECT_STREAM}")
            elif obj[TYPE] == XREF:
                placeable = XREF_STREAM in self.pdf_reader.trailer

                for k, v in self.pdf_reader.trailer.items():
                    xref_val_for_key = obj.get(k)

                    if k in [XREF_STREAM, PREV]:
                        continue
                    elif k == SIZE:
                        if xref_val_for_key is None or v != (xref_val_for_key + 1):
                            log.info(f"{XREF} has {SIZE} of {xref_val_for_key}, trailer has {SIZE} of {v}")
                            placeable = False

                        continue
                    elif k not in obj or v != obj.get(k):
                        log.info(f"Trailer has {k} -> {v} but {XREF} obj has {obj.get(k)} at that key")
                        placeable = False

                if placeable:
                    self.pdf_tree.add_child(self._build_or_find_node(ref, XREF_STREAM))
            else:
                log.warning(f"{XREF} Obj {idnum} not found in tree!")
