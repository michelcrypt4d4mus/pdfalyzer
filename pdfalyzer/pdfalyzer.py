"""
Walks the PDF objects, wrapping each in a PdfTreeNode and putting them into a tree
managed by the anytree library. Once the PDF is parsed this class manages things like
searching the tree and printing out information.
"""
from collections import defaultdict
from os.path import basename
from typing import List, Optional

from anytree import LevelOrderIter, RenderTree, SymlinkNode
from anytree.render import DoubleStyle
from anytree.search import findall, findall_by_attr
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
from PyPDF2.generic import IndirectObject, NameObject, NumberObject, StreamObject
from rich.panel import Panel
from rich.table import Column, Table
from rich.text import Text
from yaralyzer.config import YaralyzerConfig
from yaralyzer.helpers.bytes_helper import get_bytes_info
from yaralyzer.helpers.file_helper import load_binary_data
from yaralyzer.helpers.rich_text_helper import CENTER, LEFT, size_in_bytes_text
from yaralyzer.output.rich_console import BYTES_HIGHLIGHT, GREY, console
from yaralyzer.output.rich_layout_elements import bytes_hashes_table
from yaralyzer.util.logging import log

from pdfalyzer.binary.binary_scanner import BinaryScanner
from pdfalyzer.decorators.document_model_printer import print_with_header
from pdfalyzer.decorators.pdf_tree_node import PdfTreeNode
from pdfalyzer.detection.yaralyzer_helper import get_file_yaralyzer
from pdfalyzer.helpers.pdf_object_helper import get_symlink_representation
from pdfalyzer.helpers.string_helper import pp
from pdfalyzer.font_info import FontInfo
from pdfalyzer.output.layout import print_section_header, print_section_subheader, print_section_sub_subheader
from pdfalyzer.util.adobe_strings import (COLOR_SPACE, D, DEST, EXT_G_STATE, FONT, K, KIDS,
     NON_TREE_REFERENCES, NUMS, OBJECT_STREAM, OPEN_ACTION, P, PARENT, PREV, RESOURCES, SIZE,
     STRUCT_ELEM, TRAILER, TYPE, UNLABELED, XOBJECT, XREF, XREF_STREAM)
from pdfalyzer.util.exceptions import PdfWalkError

TRAILER_FALLBACK_ID = 10000000

# Some PdfObjects can't be properly placed in the tree until the entire tree is parsed
INDETERMINATE_REFERENCES = [
    COLOR_SPACE,
    DEST,
    EXT_G_STATE,
    FONT,
    OPEN_ACTION,
    RESOURCES,
    XOBJECT,
    UNLABELED, # TODO: this might be wrong? maybe this is where the /Resources actually live?
]

# A node with this label is really just a non-tree link between nodes
PURE_REFERENCE_NODE_LABELS = [
    D,
    DEST,
]


class Pdfalyzer:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_basename = basename(pdf_path)
        self.pdf_bytes = load_binary_data(pdf_path)
        self.pdf_bytes_info = get_bytes_info(self.pdf_bytes)
        pdf_file = open(pdf_path, 'rb')  # Filehandle must be left open for PyPDF2 to perform seeks
        self.pdf = PdfReader(pdf_file)
        self.yaralyzer = get_file_yaralyzer(pdf_path)

        # Initialize tracking variables
        self.indeterminate_ids = set()  # See INDETERMINATE_REFERENCES comment
        self.traversed_nodes = {}
        self.font_infos = []
        self.max_generation = 0

        # Build the tree
        self.walk_pdf()

    def walk_pdf(self):
        """
        PDFs are read trailer first so trailer is the root of the tree.
        We build the rest by recursively following references we find in nodes we encounter.
        """
        trailer = self.pdf.trailer
        self.pdf_size = trailer.get(SIZE)

        # Technically the trailer has no ID in the PDF but we set it to the /Size of the PDF for convenience
        if self.pdf_size is None:
            trailer_id = TRAILER_FALLBACK_ID
        else:
            trailer_id = self.pdf_size

        self.pdf_tree = PdfTreeNode(trailer, TRAILER, trailer_id)
        self.traversed_nodes[self.pdf_tree.idnum] = self.pdf_tree
        self.walk_node(self.pdf_tree)
        self._resolve_indeterminate_nodes()  # After scanning all the objects we place nodes whose position was uncertain
        self._extract_font_infos()
        self._verify_all_traversed_nodes_are_in_tree()
        self._verify_untraversed_nodes_are_untraversable()
        self._symlink_other_relationships()  # Create symlinks for non parent/child relationships between nodes
        log.info(f"Walk complete.")

    def walk_node(self, node: PdfTreeNode):
        """Recursively walk the PDF's tree structure starting at a given node"""
        log.info(f'walk_node() called with {node}. Object dump:\n{print_with_header(node.obj, node.label)}')
        self._ensure_safe_to_walk(node)
        references = node.references()

        for (key, address, value) in references:
            self._process_reference(node, key, address, value)

        node.all_references_processed = True

        for next_node in [self.traversed_nodes[ref.pdf_obj.idnum] for ref in references]:
            if not next_node.all_references_processed:
                self.walk_node(next_node)

    def find_node_by_idnum(self, idnum):
        """Find node with idnum in the tree. Return None if that node is not in tree or not reachable from the root."""
        nodes = [n for n in findall_by_attr(self.pdf_tree, name='idnum', value=idnum) if not isinstance(n, SymlinkNode)]

        if len(nodes) == 0:
            return None
        elif len(nodes) == 1:
            return nodes[0]
        else:
            raise PdfWalkError(f"Too many nodes had id {idnum}: {nodes}")

    def print_everything(self) -> None:
        """Print every kind of analysis on offer to Rich console"""
        self.print_document_info()
        self.print_summary()
        self.print_tree()
        self.print_rich_table_tree()
        self.print_font_info()
        self.print_other_relationships()

    def print_document_info(self) -> None:
        """Print the embedded document info (author, timestamps, version, etc)"""
        print_section_header(f'Document Info for {self.pdf_basename}')
        console.print(pp.pformat(self.pdf.getDocumentInfo()))
        console.line()
        console.print(bytes_hashes_table(self.pdf_bytes, self.pdf_basename))
        console.line()

    def print_tree(self):
        print_section_header(f'Simple tree view of {self.pdf_basename}')

        for pre, _fill, node in RenderTree(self.pdf_tree, style=DoubleStyle):
            if isinstance(node, SymlinkNode):
                symlink_rep = get_symlink_representation(node.parent, node)
                console.print(pre + f"[{symlink_rep.style}]{symlink_rep.text}[/{symlink_rep.style}]")
            else:
                console.print(Text(pre) + node.__rich__())

        console.print("\n\n")

    def print_rich_table_tree(self) -> None:
        print_section_header(f'Rich tree view of {self.pdf_basename}')
        console.print(self.pdf_tree.generate_rich_tree())

    def print_summary(self) -> None:
        print_section_header(f'PDF Node Summary for {self.pdf_basename}')
        console.print_json(data=self._analyze_tree(), sort_keys=True)

    def print_font_info(self, font_idnum=None) -> None:
        print_section_header(f'{len(self.font_infos)} fonts found in {self.pdf_basename}')

        for font_info in [fi for fi in self.font_infos if font_idnum is None or font_idnum == fi.idnum]:
            font_info.print_summary()

    def print_streams_analysis(self, idnum: Optional[int] = None) -> None:
        print_section_header(f'Binary Stream Analysis / Extraction')
        console.print(self.stream_objects_table())

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

            print_section_subheader(f"{node} Summary and Analysis", style=f"{BYTES_HIGHLIGHT} reverse")
            binary_scanner = BinaryScanner(node_stream_bytes, node)
            console.print(bytes_hashes_table(binary_scanner.bytes))
            binary_scanner.print_stream_preview()
            binary_scanner.check_for_dangerous_instructions()

            if not YaralyzerConfig.SUPPRESS_DECODES:
                binary_scanner.check_for_boms()
                binary_scanner.force_decode_all_quoted_bytes()

            binary_scanner.print_decoding_stats_table()

    def print_yara_results(self, font_idnum=None) -> None:
        print_section_header(f"YARA Scan of PDF rules for '{self.pdf_basename}'")
        self.yaralyzer.yaralyze()

        # TODO: we should really scan all the binary streams not just those in the fonts
        for font_info in [fi for fi in self.font_infos if font_idnum is None or font_idnum == fi.idnum]:
            font_info.yara_scan()

    def print_other_relationships(self) -> None:
        """Print the inter-node, non-tree relationships for all nodes in the tree"""
        console.print("\n\n")
        console.print(Panel(f"Other Relationships", expand=False), style='reverse')

        for node in LevelOrderIter(self.pdf_tree):
            if len(node.other_relationships) == 0:
                continue

            console.print("\n")
            console.print(Panel(f"Non tree relationships for {node}", expand=False))
            node.print_other_relationships()

    def stream_objects_table(self) -> Table:
        table = Table('Stream Length', 'Node')
        table.columns[0].justify = 'right'

        for node in self.stream_nodes():
            table.add_row(size_in_bytes_text(node.stream_length), node.__rich__())

        return table

    def stream_nodes(self) -> List[PdfTreeNode]:
        """List of actual nodes (not SymlinkNodes) containing streams sorted by PDF object ID"""
        stream_filter = lambda node: node.contains_stream() and not isinstance(node, SymlinkNode)
        return sorted(findall(self.pdf_tree, stream_filter), key=lambda r: r.idnum)

    def _process_reference(self, node: PdfTreeNode, key: str, address: str, reference: IndirectObject) -> [PdfTreeNode]:
        """Place the referenced node in the tree. Returns a list of nodes to walk next."""
        self.max_generation = max([self.max_generation, reference.generation or 0])
        seen_before = (reference.idnum in self.traversed_nodes)
        referenced_node = self._build_or_find_node(reference, address)
        reference_log_string = f"{node} reference at {address} to {referenced_node}"
        log.info(f'Assessing {reference_log_string}...')
        references_to_return = []

        # If one is already a parent/child of the other there's nothing to do
        if referenced_node == node.parent or referenced_node in node.children:
            log.debug(f"  {node} and {referenced_node} are already related")
            return []

        # If there's an explicit /Parent or /Kids reference then we know the correct relationship
        if key in [PARENT, KIDS] or (node.type == STRUCT_ELEM and key in [K, P]):
            if key in [PARENT, P]:
                node.set_parent(referenced_node)
            else:
                node.add_child(referenced_node)

            if reference.idnum in self.indeterminate_ids:
                log.info(f"  Found refefence {address} => {node} of previously indeterminate node {referenced_node}")
                self.indeterminate_ids.remove(reference.idnum)

            if not seen_before:
                references_to_return = [referenced_node]

        # Non tree references are not children or parents.
        # TODO: Checking startswith(NUMS) is a hack that probably will not cover all cases with /StructElem
        elif key in NON_TREE_REFERENCES or node.label.startswith(NUMS) or node.label in PURE_REFERENCE_NODE_LABELS:
            log.debug(f"{reference_log_string} is a non tree reference.")
            referenced_node.add_relationship(node, address)

            if not self.find_node_by_idnum(referenced_node.idnum):
                references_to_return = [referenced_node]

        # Indeterminate references need to wait until everything has been scanned to be placed
        elif key in INDETERMINATE_REFERENCES and key == address:
            log.info(f'  Indeterminate {reference_log_string}')
            referenced_node.add_relationship(node, address)
            self.indeterminate_ids.add(referenced_node.idnum)
            return [referenced_node]

        # If we've seen the node before it should have a parent or be indeterminate
        elif seen_before:
            if reference.idnum not in self.indeterminate_ids and referenced_node.parent is None:
                raise PdfWalkError(f"{reference_log_string} - ref has no parent and is not indeterminate")

            referenced_node.add_relationship(node, address)

        # If no other conditions are met, add the reference as a child
        else:
            node.add_child(referenced_node)
            references_to_return = [referenced_node]

        return references_to_return

    def _symlink_other_relationships(self):
        """Create SymlinkNodes for relationships between PDF objects that are not parent/child relationships"""
        for node in LevelOrderIter(self.pdf_tree):
            if node.other_relationship_count() == 0 or isinstance(node, SymlinkNode):
                continue

            log.info(f"Symlinking {node}'s {node.other_relationship_count()} other relationships...")

            for relationship in node.other_relationships:
                log.debug(f"   * Linking {relationship}")
                SymlinkNode(node, parent=relationship.from_node)

    def _resolve_indeterminate_nodes(self) -> None:
        """
        Some nodes cannot be placed until we have walked the rest of the tree. For instance
        if we encounter a /Page that references /Resources we need to know if there's a
        /Pages parent of the /Page before committing to a tree structure.
        """
        indeterminate_nodes = [self.traversed_nodes[idnum] for idnum in self.indeterminate_ids]
        indeterminate_nodes_string = "\n   ".join([f"{node}" for node in indeterminate_nodes])
        log.info(f"Resolving {len(indeterminate_nodes)} indeterminate nodes: {indeterminate_nodes_string}")

        for idnum in self.indeterminate_ids:
            if self.find_node_by_idnum(idnum):
                log.warning(f"Node with ID {idnum} marked indeterminate but found in tree...")
                continue

            set_lowest_id_node_as_parent = False
            node = self.traversed_nodes[idnum]
            referenced_by_keys = list(set([r.reference_key for r in node.other_relationships]))
            log.info(f"Attempting to resolve indeterminate node {node}")

            if node.label == RESOURCES:
                self._place_resources_node(node)
                continue
            elif len(referenced_by_keys) == 1:
                log.info(f"{node}'s other relationships all use key {referenced_by_keys[0]}, linking to lowest id")
                set_lowest_id_node_as_parent = True
                possible_parents = node.other_relationships
            elif len(referenced_by_keys) == 2 and (referenced_by_keys[0] in referenced_by_keys[1] or referenced_by_keys[1] in referenced_by_keys[0]):
                log.info(f"{node}'s other relationships ref keys are same except slice: {referenced_by_keys}, linking to lowest id")
                set_lowest_id_node_as_parent = True
                possible_parents = node.other_relationships
            elif any(r.from_node.label == RESOURCES for r in node.other_relationships) and \
                    all(any(r.from_node.label.startswith(ir) for ir in INDETERMINATE_REFERENCES) for r in node.other_relationships):
                log.info(f"Linking {node} to lowest id {RESOURCES} node...")
                possible_parents = [r for r in node.other_relationships if r.from_node.label == RESOURCES]
                set_lowest_id_node_as_parent = True
            else:
                determinate_relations = [r for r in node.other_relationships if r.from_node.label not in INDETERMINATE_REFERENCES]
                determinate_refkeys = set([r.from_node.label for r in determinate_relations])

                if len(determinate_refkeys) == 1:
                    ref_key = determinate_relations[0].reference_key
                    log.info(f"Only one ref key {ref_key} that's determinate, choose parent as lowest id using it")
                    possible_parents = determinate_relations
                    set_lowest_id_node_as_parent = True

            if set_lowest_id_node_as_parent:
                lowest_idnum = min([r.from_node.idnum for r in possible_parents])
                lowest_id_relationship = next(r for r in node.other_relationships if r.from_node.idnum == lowest_idnum)
                log.info(f"Setting parent of {node} to {lowest_id_relationship}")
                node.set_parent(self.traversed_nodes[lowest_idnum])
                continue

            self.print_tree()
            log.fatal("Dumped tree status for debugging.")
            node.print_other_relationships()
            raise PdfWalkError(f"Cannot place {node}")

    def _extract_font_infos(self) -> None:
        """Extract information about fonts in the tree and place it in self.font_infos"""
        for node in LevelOrderIter(self.pdf_tree):
            if isinstance(node.obj, dict) and RESOURCES in node.obj:
                log.debug(f"Extracting fonts from node with '{RESOURCES}' key: {node}...")
                known_font_ids = [fi.idnum for fi in self.font_infos]

                self.font_infos += [
                    fi for fi in FontInfo.extract_font_infos(node.obj)
                    if fi.idnum not in known_font_ids
                ]

    def _ensure_safe_to_walk(self, node) -> None:
        if not node.idnum in self.traversed_nodes:
            return

        if self.traversed_nodes[node.idnum] != node:
            raise PdfWalkError("Duplicate PDF object ID {node.idnum}")

    def _place_resources_node(self, resources_node) -> None:
        """See if there is a common ancestor like /Pages; if so that's the parent"""
        for relationship in resources_node.other_relationships:
            other_relationships = [r for r in resources_node.other_relationships if r != relationship]

            if all(relationship[0] in r[0].ancestors for r in other_relationships):
                log.info(f'{relationship[0]} is the common ancestor found while placing /Resources')
                resources_node.set_parent(relationship[0])
                return

        log.error(f"Failed to place {resources_node}. {RESOURCES} relationship dump:")
        resources_node.print_other_relationships()
        raise PdfWalkError(f'Failed to place {resources_node}')

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

        for node in LevelOrderIter(self.pdf_tree):
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

    def _print_traversed_nodes(self) -> None:
        """Debug method that displays which nodes have already been walked"""
        for i in sorted(self.traversed_nodes.keys()):
            console.print(f'{i}: {self.traversed_nodes[i]}')

    def _verify_all_traversed_nodes_are_in_tree(self) -> None:
        """Make sure every node we can see is reachable from the root of the tree"""
        missing_nodes = [node for idnum, node in self.traversed_nodes.items() if self.find_node_by_idnum(idnum) is None]

        if len(missing_nodes) > 0:
            msg = f"Nodes were traversed but never placed: {missing_nodes}"
            console.print(msg)
            raise PdfWalkError(msg)

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

            ref = IndirectObject(idnum, self.max_generation, self.pdf)
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
                placeable = XREF_STREAM in self.pdf.trailer

                for k, v in self.pdf.trailer.items():
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
