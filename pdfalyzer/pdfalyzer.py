"""
Walks the PDF objects, wrapping each in a PdfTreeNode and putting them into a tree
managed by the anytree library. Once the PDF is parsed this class manages things like
searching the tree and printing out information.
"""
from collections import defaultdict
from os.path import basename
from typing import Dict, Iterator, List, Optional

from anytree import LevelOrderIter, RenderTree, SymlinkNode
from anytree.render import DoubleStyle
from anytree.search import findall, findall_by_attr
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
from PyPDF2.generic import IndirectObject, NameObject, NumberObject
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from yaralyzer.config import YaralyzerConfig
from yaralyzer.helpers.bytes_helper import get_bytes_info
from yaralyzer.helpers.file_helper import load_binary_data
from yaralyzer.output.rich_console import BYTES_HIGHLIGHT, console
from yaralyzer.output.rich_layout_elements import bytes_hashes_table
from yaralyzer.util.logging import log

from pdfalyzer.binary.binary_scanner import BinaryScanner
from pdfalyzer.decorators.document_model_printer import print_with_header
from pdfalyzer.decorators.pdf_tree_node import DECODE_FAILURE_LEN, PdfTreeNode
from pdfalyzer.detection.yaralyzer_helper import get_file_yaralyzer
from pdfalyzer.font_info import FontInfo
from pdfalyzer.helpers.string_helper import is_prefixed_by_any, pp
from pdfalyzer.detection.yaralyzer_helper import get_bytes_yaralyzer
from pdfalyzer.output.layout import print_section_header, print_section_subheader, print_section_sub_subheader
from pdfalyzer.output.pdf_node_rich_table import generate_rich_tree, get_symlink_representation
from pdfalyzer.output.stream_objects_table import stream_objects_table
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
        self.yaralyzer = get_file_yaralyzer(pdf_path)
        # Initialize tracking variables
        self.indeterminate_ids = set()  # See INDETERMINATE_REFERENCES comment
        self.traversed_nodes: Dict[int, PdfTreeNode] = {}  # Nodes we've seen already
        self.font_infos: List[FontInfo] = []  # Font summary objects
        self.max_generation = 0  # PDF revisions are "generations"; this is the max generation encountered
        self.walk_pdf()  # Build the tree

    def walk_pdf(self):
        """
        PDFs are always read trailer first so trailer is the root of the tree.
        We build the rest by recursively following references we find in nodes we encounter.
        """
        trailer = self.pdf_reader.trailer
        self.pdf_size = trailer.get(SIZE)
        # Technically the trailer has no ID in the PDF but we set it to the /Size of the PDF for convenience
        trailer_id = self.pdf_size if self.pdf_size is not None else TRAILER_FALLBACK_ID
        self.pdf_tree = PdfTreeNode(trailer, TRAILER, trailer_id)
        self.traversed_nodes[self.pdf_tree.idnum] = self.pdf_tree
        self.walk_node(self.pdf_tree)
        self._resolve_indeterminate_nodes()  # After scanning all objects we place nodes whose position was uncertain
        self._extract_font_infos()
        self._verify_all_traversed_nodes_are_in_tree()
        self._verify_untraversed_nodes_are_untraversable()
        self._symlink_non_tree_relationships()  # Create symlinks for non parent/child relationships between nodes
        log.info(f"Walk complete.")

    def walk_node(self, node: PdfTreeNode) -> None:
        """Recursively walk the PDF's tree structure starting at a given node"""
        log.info(f'walk_node() called with {node}. Object dump:\n{print_with_header(node.obj, node.label)}')
        self._ensure_safe_to_walk(node)
        references = node.references_to_other_nodes()

        for reference in references:
            self._process_reference(reference)

        node.all_references_processed = True

        for next_node in [self.traversed_nodes[ref.to_obj.idnum] for ref in references]:
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

    def print_everything(self) -> None:
        """Print every kind of analysis on offer to Rich console."""
        self.print_document_info()
        self.print_summary()
        self.print_tree()
        self.print_rich_table_tree()
        self.print_font_info()
        self.print_non_tree_relationships()

    def print_document_info(self) -> None:
        """Print the embedded document info (author, timestamps, version, etc)."""
        print_section_header(f'Document Info for {self.pdf_basename}')
        console.print(pp.pformat(self.pdf_reader.getDocumentInfo()))
        console.line()
        console.print(bytes_hashes_table(self.pdf_bytes, self.pdf_basename))
        console.line()
        console.print(self._stream_objects_table())
        console.line()

    def print_tree(self) -> None:
        """Print the simple view of the PDF tree."""
        print_section_header(f'Simple tree view of {self.pdf_basename}')

        for pre, _fill, node in RenderTree(self.pdf_tree, style=DoubleStyle):
            if isinstance(node, SymlinkNode):
                symlink_rep = get_symlink_representation(node.parent, node)
                console.print(pre + f"[{symlink_rep.style}]{symlink_rep.text}[/{symlink_rep.style}]")
            else:
                console.print(Text(pre) + node.__rich__())

        self._verify_all_traversed_nodes_are_in_tree()
        console.print("\n\n")

    def print_rich_table_tree(self) -> None:
        """Print the rich view of the PDF tree."""
        print_section_header(f'Rich tree view of {self.pdf_basename}')
        console.print(generate_rich_tree(self.pdf_tree))
        self._verify_all_traversed_nodes_are_in_tree()

    def print_summary(self) -> None:
        print_section_header(f'PDF Node Summary for {self.pdf_basename}')
        console.print_json(data=self._analyze_tree(), sort_keys=True)

    def print_font_info(self, font_idnum=None) -> None:
        print_section_header(f'{len(self.font_infos)} fonts found in {self.pdf_basename}')

        for font_info in [fi for fi in self.font_infos if font_idnum is None or font_idnum == fi.idnum]:
            font_info.print_summary()

    def print_streams_analysis(self, idnum: Optional[int] = None) -> None:
        print_section_header(f'Binary Stream Analysis / Extraction')
        console.print(self._stream_objects_table())

        for node in [n for n in self.stream_nodes() if idnum is None or idnum == n.idnum]:
            node_stream_bytes = node.stream_data

            if node_stream_bytes is None or node.stream_length == 0:
                print_section_sub_subheader(f"{node} stream has length 0", style='dim')
                continue

            if not isinstance(node_stream_bytes, bytes):
                msg = f"Stream in {node} is not bytes, it's {type(node.stream_data)}. Will reencode for YARA " + \
                       "but they may not be the same bytes as the original stream!"
                log.warning(msg)
                node_stream_bytes = node_stream_bytes.encode()

            print_section_subheader(f"{escape(str(node))} Summary and Analysis", style=f"{BYTES_HIGHLIGHT} reverse")
            binary_scanner = BinaryScanner(node_stream_bytes, node)
            console.print(bytes_hashes_table(binary_scanner.bytes))
            binary_scanner.print_stream_preview()
            binary_scanner.check_for_dangerous_instructions()

            if not YaralyzerConfig.SUPPRESS_DECODES:
                binary_scanner.check_for_boms()
                binary_scanner.force_decode_all_quoted_bytes()

            binary_scanner.print_decoding_stats_table()

    def print_yara_results(self) -> None:
        print_section_header(f"YARA Scan of PDF rules for '{self.pdf_basename}'")
        self.yaralyzer.yaralyze()
        console.line(2)

        for node in self.stream_nodes():
            if node.stream_length == DECODE_FAILURE_LEN:
                log.warning(f"{node} binary stream could not be extracted")
            elif node.stream_length == 0 or node.stream_data is None:
                log.debug(f"No binary to scan for {node}")
            else:
                get_bytes_yaralyzer(node.stream_data, str(node)).yaralyze()
                console.line(2)

    def print_non_tree_relationships(self) -> None:
        """Print the inter-node, non-tree relationships for all nodes in the tree"""
        console.line(2)
        console.print(Panel(f"Other Relationships", expand=False), style='reverse')

        for node in LevelOrderIter(self.pdf_tree):
            if len(node.non_tree_relationships) == 0:
                continue

            console.print("\n")
            console.print(Panel(f"Non tree relationships for {node}", expand=False))
            node.print_non_tree_relationships()

    def stream_nodes(self) -> List[PdfTreeNode]:
        """List of actual nodes (not SymlinkNodes) containing streams sorted by PDF object ID"""
        stream_filter = lambda node: node.contains_stream() and not isinstance(node, SymlinkNode)
        return sorted(findall(self.pdf_tree, stream_filter), key=lambda r: r.idnum)

    def is_in_tree(self, search_for_node: PdfTreeNode) -> bool:
        """Returns true if search_for_node is in the tree already."""
        for node in self.level_order_node_iterator():
            if node == search_for_node:
                return True

        return False

    def level_order_node_iterator(self) -> Iterator[PdfTreeNode]:
        """Iterate over nodes, grouping them by distance from the root."""
        return LevelOrderIter(self.pdf_tree)

    # TODO: should maybe be on PdfTreeNode class
    def _process_reference(self, reference: PdfObjectRelationship) -> List[PdfTreeNode]:
        """
        Place the referenced 'node' in the tree. Returns a list of nodes to walk next.
        'address' is the key used in node.obj to refer to 'reference' object
           plus any modifiers like [2] or [/Something]
        """
        log.debug(f'Assessing {reference.from_node} reference {reference}...')
        was_seen_before = (reference.to_obj.idnum in self.traversed_nodes) # Must come before _build_or_find()
        from_node = reference.from_node
        to_node = self._build_or_find_node(reference.to_obj, reference.address)
        self.max_generation = max([self.max_generation, reference.to_obj.generation or 0])

        # If one is already a parent/child of the other there's nothing to do
        if to_node == from_node.parent or to_node in from_node.children:
            log.debug(f"  {from_node} and {to_node} are already related")
            return []

        # If there's an explicit /Parent or /Kids reference then we know the correct relationship
        if reference.is_parent or reference.is_child:
            if reference.is_parent:
                from_node.set_parent(to_node)
            else:
                from_node.add_child(to_node)

            if reference.to_obj.idnum in self.indeterminate_ids:
                log.info(f"  Found reference {reference} => {from_node} of previously indeterminate node {to_node}")
                self.indeterminate_ids.remove(reference.to_obj.idnum)

            if was_seen_before:
                return []
        elif reference.is_indeterminate or reference.is_link or was_seen_before:
            to_node.add_non_tree_relationship(reference)

            # Indeterminate references need to wait until everything has been scanned to be placed
            if reference.is_indeterminate or (reference.is_link and not self.is_in_tree(to_node)):
                log.info(f'  Indeterminate ref {reference}')
                self.indeterminate_ids.add(to_node.idnum)
            elif reference.is_link:
                log.debug(f"  Link ref {reference}")  # Link nodes like /Dest are usually just links between nodes
                return []
            elif reference.to_obj.idnum not in self.indeterminate_ids and to_node.parent is None:
                raise PdfWalkError(f"{reference} - ref has no parent and is not indeterminate")
            else:
                log.debug(f"  Already saw {reference}; not scanning next")
                return []
        # If no other conditions are met, add the reference as a child
        else:
            from_node.add_child(to_node)

        log.debug(f"Node to walk next: {to_node}")
        return [to_node]

    def _symlink_non_tree_relationships(self) -> None:
        """Create SymlinkNodes for relationships between PDF objects that are not parent/child relationships"""
        for node in self.level_order_node_iterator():
            if node.non_tree_relationship_count() == 0 or isinstance(node, SymlinkNode):
                continue

            log.info(f"Symlinking {node}'s {node.non_tree_relationship_count()} other relationships...")

            # TODO: this should probably be in the PdfTreeNode class
            for relationship in node.non_tree_relationships:
                log.debug(f"   Linking {relationship} to {node}")
                SymlinkNode(node, parent=relationship.from_node)

    def _resolve_indeterminate_nodes(self) -> None:
        """
        Some nodes cannot be placed until we have walked the rest of the tree. For instance
        if we encounter a /Page that references /Resources we need to know if there's a
        /Pages parent of the /Page before committing to a tree structure.
        TODO: this method sucks.
        """
        indeterminate_nodes = [self.traversed_nodes[idnum] for idnum in self.indeterminate_ids]
        indeterminate_nodes_string = "\n   ".join([f"{node}" for node in indeterminate_nodes])
        log.info(f"Resolving {len(indeterminate_nodes)} indeterminate nodes: {indeterminate_nodes_string}")

        for node in indeterminate_nodes:
            # We're basically checking for situations where we can just pick the lowest ID object that
            # has a relationship to the indeterminate node. In rare cases we will override 'possible_parent_relationships'.
            log.debug(f"Attempting to resolve indeterminate node {node}")
            set_lowest_id_node_as_parent = True
            possible_parent_relationships = node.non_tree_relationships # TODO 'possible_parent_relationships'
            addresses = node.unique_addresses()
            # TODO: this name sucks
            related_node_unique_labels = node.unique_labels_of_non_tree_referencers()
            common_ancestor_among_possible_parents = node.common_ancestor_among_non_tree_relationships()

            # TODO we should have removed the node from indeterminate_node_ids before this point
            if node.parent is not None:
                log.info(f"{node} marked indeterminate but already has parent: {node.parent}")
                continue

            if common_ancestor_among_possible_parents is not None:
                log.debug(f"  Found common ancestor: {common_ancestor_among_possible_parents}")
                node.set_parent(common_ancestor_among_possible_parents)
                continue
            elif len(related_node_unique_labels) == 1:
                log.info(f"Single label for all of {node}'s relationships; setting parent as lowest id")
            elif node.label == COLOR_SPACE:
                log.info("Color space node found; placing at lowest ID")
            elif len(addresses) == 1:
                log.info(f"{node}'s other relationships all use key {addresses[0]}, linking to lowest id")
            elif all([EXTERNAL_GRAPHICS_STATE_REGEX.match(key) for key in addresses]):
                log.info(f"{node}'s other relationships are all {EXT_G_STATE} refs; linking to lowest id")
            elif len(addresses) == 2 and (addresses[0] in addresses[1] or addresses[1] in addresses[0]):
                log.info(f"{node}'s other relationships ref keys are same except slice: {addresses}, linking to lowest id")
            elif any(r.from_node.label == RESOURCES for r in node.non_tree_relationships) and \
                    all(is_prefixed_by_any(r.from_node.label, INDETERMINATE_REFERENCES) for r in node.non_tree_relationships):
                msg = f"{node} referred to from {RESOURCES} labeled node; all other relationships are indeterminate. "
                msg += f"Choosing lowest id {RESOURCES} node among them as parent..."
                possible_parent_relationships = [r for r in node.non_tree_relationships if r.from_node.label == RESOURCES]
            elif node.label.startswith(RESOURCES) and related_node_unique_labels == set([PAGE, PAGES]):
                # An edge case seen in the wild involving a PDF that doesn't conform to the PDF spec
                log.warning(f"Failed to place {node}; seems to be a loose {PAGE}. Linking to first {PAGES}")
                pages_nodes = [n for n in node.nodes_with_non_tree_references_to_self() if node.type == PAGES]
                node.set_parent(sorted(pages_nodes, key=lambda n: n.idnum)[0])
                continue
            else:
                possible_parent_relationships = [
                    r for r in node.non_tree_relationships
                    if r.from_node.label not in INDETERMINATE_REFERENCES
                ]

                determinate_refkeys = set([r.from_node.label for r in possible_parent_relationships])

                if len(determinate_refkeys) == 1:
                    msg = f"1 ref_key {possible_parent_relationships[0].reference_key} is determinate, parent is lowest id using it"
                    log.info(msg)
                else:
                    set_lowest_id_node_as_parent= False

            if not set_lowest_id_node_as_parent:
                self.print_tree()
                log.error(f"{node} relationship dump:")
                node.log_non_tree_relationships()
                log.error(f"Failed to place {node} referenced from nodes w/labels: {list(related_node_unique_labels)}")
                log.error(f"   Referenced by addresses: {node.unique_addresses()}")
                log.fatal("Dumped tree status and non_tree_relationships for debugging!")
                raise PdfWalkError(f"Cannot place {node}")

            lowest_idnum = min([r.from_node.idnum for r in possible_parent_relationships])
            lowest_id_relationship = next(r for r in node.non_tree_relationships if r.from_node.idnum == lowest_idnum)
            log.info(f"Setting parent of {node} to {lowest_id_relationship}")
            node.set_parent(self.traversed_nodes[lowest_idnum])

    def _extract_font_infos(self) -> None:
        """Extract information about fonts in the tree and place it in self.font_infos"""
        for node in self.level_order_node_iterator():
            if isinstance(node.obj, dict) and RESOURCES in node.obj:
                log.debug(f"Extracting fonts from node with '{RESOURCES}' key: {node}...")
                known_font_ids = [fi.idnum for fi in self.font_infos]

                self.font_infos += [
                    fi for fi in FontInfo.extract_font_infos(node.obj)
                    if fi.idnum not in known_font_ids
                ]

    def _ensure_safe_to_walk(self, node: PdfTreeNode) -> None:
        """Assert that we haven't traversed this node or if we have it has the same ID."""
        assert node.idnum not in self.traversed_nodes or self.traversed_nodes[node.idnum] == node

    def _build_or_find_node(self, reference: IndirectObject, reference_key: str) -> PdfTreeNode:
        """If node exists in self.traversed_nodes return it, otherwise build a node"""
        if reference.idnum in self.traversed_nodes:
            return self.traversed_nodes[reference.idnum]

        # TODO: known_to_parent_as should not be passed for non-child relationships even though as it
        #       stands it is corrected later when the true parent is found.
        log.debug(f"Building node for {reference_key} -> {reference}")
        new_node = PdfTreeNode.from_reference(reference, reference_key)
        self.traversed_nodes[reference.idnum] = new_node
        return new_node

    def _analyze_tree(self) -> dict:
        """Generate a dict with some basic data points about the PDF tree"""
        pdf_object_types = defaultdict(int)
        node_labels = defaultdict(int)
        keys_encountered = defaultdict(int)
        node_count = 0

        for node in self.level_order_node_iterator():
            pdf_object_types[type(node.obj).__name__] += 1
            node_labels[node.label] += 1
            node_count += 1

            if isinstance(node.obj, dict):
                for k in node.obj.keys():
                    keys_encountered[k] += 1

        return {
            'keys_encountered': keys_encountered,
            'node_count': node_count,
            'node_labels': node_labels,
            'pdf_object_types': pdf_object_types,
        }

    def _stream_objects_table(self) -> Table:
        return stream_objects_table(self.stream_nodes())

    def _print_traversed_nodes(self) -> None:
        """Debug method that displays which nodes have already been walked"""
        for i in sorted(self.traversed_nodes.keys()):
            console.print(f'{i}: {self.traversed_nodes[i]}')

    def _verify_all_traversed_nodes_are_in_tree(self) -> None:
        """Make sure every node we can see is reachable from the root of the tree"""
        missing_nodes = [
            node for idnum, node in self.traversed_nodes.items()
            if self.find_node_by_idnum(idnum) is None
        ]

        if len(missing_nodes) > 0:
            msg = f"Nodes were traversed but never placed: {escape(str(missing_nodes))}\n" + \
                   "For link nodes like /First, /Next, /Prev, and /Last this might be no big deal - depends " + \
                   "on the PDF. But for other node typtes this could indicate missing data in the tree."
            console.print(msg)
            log.warning(msg)

    def _verify_untraversed_nodes_are_untraversable(self) -> None:
        """Make sure any PDF object IDs we can't find in tree are /ObjStm or /Xref nodes"""
        if self.pdf_size is None:
            log.warning(f"{SIZE} not found in PDF trailer; cannot verify all nodes are in tree")
            return

        if self.max_generation > 0:
            log.warning(f"_verify_untraversed_nodes_are_untraversable() only checking generation {self.max_generation}")

        for idnum in [i + 1 for i in range(self.pdf_size)]:
            if self.find_node_by_idnum(idnum) is not None:
                log.debug(f"Verified object {idnum} is in tree")
                continue

            ref = IndirectObject(idnum, self.max_generation, self.pdf_reader)

            try:
                obj = ref.get_object()
            except PdfReadError as e:
                if 'Invalid Elementary Object' in str(e):
                    log.info(f"Couldn't verify elementary obj with id {idnum} is properly in tree")
                    continue
                else:
                    log.error(str(e))
                    console.print(str(e), style='error')
                    console.print_exception()
                    raise

            if obj is None:
                log.error(f"Cannot find ref {ref} in PDF!")
                continue
            elif isinstance(obj, (NumberObject, NameObject)):
                log.info(f"Obj {idnum} is a {type(obj)} w/value {obj}; if referenced by /Length etc. this is a nonissue but maybe worth doublechecking")
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
