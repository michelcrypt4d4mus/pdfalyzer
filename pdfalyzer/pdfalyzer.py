"""
PDFalyzer: Analyze and explore the structure of PDF files.
"""
import time
from dataclasses import dataclass, field
from io import BufferedReader
from pathlib import Path
from typing import Iterator

from anytree import LevelOrderIter, SymlinkNode
from anytree.search import findall, findall_by_attr
from pypdf import PdfReader
from pypdf.errors import DependencyError, FileNotDecryptedError, PdfReadError
from pypdf.generic import DictionaryObject, IndirectObject
from rich.prompt import Prompt
from rich.text import Text
from yaralyzer.output.console import console
from yaralyzer.output.file_hashes_table import BytesInfo
from yaralyzer.util.exceptions import print_fatal_error, print_fatal_error_and_exit
from yaralyzer.util.logging import log_trace

from pdfalyzer.config import PdfalyzerConfig
from pdfalyzer.decorators.document_model_printer import highlighted_raw_pdf_obj_str
from pdfalyzer.decorators.indeterminate_node import IndeterminateNode
from pdfalyzer.decorators.pdf_tree_node import PdfTreeNode
from pdfalyzer.decorators.pdf_tree_verifier import PdfTreeVerifier
from pdfalyzer.font_info import FontInfo
from pdfalyzer.util.helpers.pdf_object_helper import RefAndObj, describe_obj
from pdfalyzer.pdf_object_relationship import PdfObjectRelationship
from pdfalyzer.util import adobe_strings
from pdfalyzer.util.argument_parser import is_pdfalyze_script
from pdfalyzer.util.exceptions import PdfWalkError
from pdfalyzer.util.logging import log  # Triggers log setup
from pdfalyzer.util.pdf_parser_manager import PdfParserManager

MISSING_NODE_WARN_THRESHOLD = 200
NODE_COUNT_WARN_THRESHOLD = 10_000
PASSWORD_PROMPT = Text(f"\nThis PDF is encrypted. What's the password?", style='bright_cyan bold')
TRAILER_FALLBACK_ID = 10_000_000
PYPDF_ERROR_MSG = "Failed to open file with PyPDF. Consider filing a PyPDF bug report: https://github.com/py-pdf/pypdf/issues"


@dataclass
class Pdfalyzer:
    """
    Walks a PDF's internals and builds the PDF logical structure tree.

    Each of the PDF's internal objects is wrapped in a `PdfTreeNode` object. The tree is managed
    by the `anytree` library. Information about the tree as a whole is stored in this class.
    Once the PDF is parsed this class provides access to info about or from the underlying PDF tree.

    Args:
        pdf_path (str): Path to the PDF file
        password (str | None): Password used to decrypt the PDF (if it's encrypted)

    Attributes:
        font_infos (list[FontInfo]): Font summary objects
        font_info_extraction_error (Exception | None): Error encountered extracting FontInfo (if any)
        max_generation (int): Max revision number ("generation") encounted in this PDF.
        nodes_encountered (dict[int, PdfTreeNode]): Nodes we've traversed already even if not in tree yet.
        pdf_bytes (bytes): PDF binary data.
        pdf_bytes_info (BytesInfo): File size, hashes, and other data points about the PDF's raw bytes.
        pdf_filehandle (BufferedReader): File handle that reads the PDF.
        pdf_size (int): Number of nodes as extracted from the PDF's Trailer node.
        pdf_tree (PdfTreeNode): The top node of the PDF data structure tree.
        verifier (PdfTreeVerifier): PdfTreeVerifier that can validate the PDF has been walked successfully.
        _indeterminate_ids (set[int]): See INDETERMINATE_REF_KEYS comment
        _tree_nodes (dict[int, PdfTreeNode): ID cache for nodes that are in the tree
    """
    pdf_path: Path
    password: str | None = None

    # Non-arguments:
    font_infos: list[FontInfo] = field(default_factory=list)
    font_info_extraction_error: Exception | None = None
    idnums_found_by_parser: list[int] | None = None
    max_generation: int = 0
    nodes_encountered: dict[int, PdfTreeNode] = field(default_factory=dict)
    num_nodes: int | None = None
    pdf_bytes: bytes = field(init=False)
    pdf_bytes_info: BytesInfo = field(init=False)
    pdf_filehandle: BufferedReader = field(init=False)
    pdf_reader: PdfReader = field(init=False)
    pdf_tree: PdfTreeNode = field(init=False)
    verifier: PdfTreeVerifier = field(init=False)
    _indeterminate_ids: set[int] = field(default_factory=set)
    _tree_nodes: dict[int, PdfTreeNode | None] = field(default_factory=dict)

    @property
    def pdf_basename(self):
        return self.pdf_path.name

    def __post_init__(self):
        self.pdf_path = Path(self.pdf_path)
        started_at = time.perf_counter()

        try:
            self.pdf_filehandle = open(self.pdf_path, 'rb')  # Filehandle must stay open so PyPDF can perform seeks
            self.pdf_reader = PdfReader(self.pdf_filehandle)
        except DependencyError as e:
            self._handle_fatal_error(f"Missing dependency required for this file.", e)
        except FileNotFoundError as e:
            self._handle_fatal_error(f"Invalid file", e)
        except PdfReadError as e:
            self._handle_fatal_error(f'PdfReadError: "{self.pdf_path}" doesn\'t seem to be a valid PDF file.', e)
        except Exception as e:
            console.print_exception()
            self._handle_fatal_error(f"{PYPDF_ERROR_MSG}", e)

        if self.pdf_reader.is_encrypted:
            if not self.pdf_reader.decrypt(self.password or Prompt.ask(PASSWORD_PROMPT)):
                self._handle_fatal_error(f"Wrong password", FileNotDecryptedError("encrypted PDF"))

        # Load bytes etc
        self.pdf_bytes = self.pdf_path.read_bytes()
        self.pdf_bytes_info = BytesInfo(self.pdf_bytes)

        # Bootstrap the root of the tree with the trailer. PDFs are always read trailer first.
        # Technically the trailer has no PDF Object ID but we set it to the /Size of the PDF.
        trailer = self.pdf_reader.trailer
        self.num_nodes = trailer.get(adobe_strings.SIZE)
        trailer_id = self.num_nodes if self.num_nodes is not None else TRAILER_FALLBACK_ID
        self.pdf_tree = PdfTreeNode.from_obj(trailer, adobe_strings.TRAILER, trailer_id)
        self.nodes_encountered[self.pdf_tree.idnum] = self.pdf_tree

        if not self.num_nodes:
            log.warning(f"Could not determine number of nodes in this PDF!")
        elif self.num_nodes > NODE_COUNT_WARN_THRESHOLD:
            log.warning(f"This PDF has {self.num_nodes:,} nodes; could take a while to parse...")

        # Build tree by recursively following relationships between nodes
        self.walk_node(self.pdf_tree)

        # After scanning all objects we place nodes whose position was uncertain, extract fonts, and verify
        self._resolve_indeterminate_nodes()
        self._resolve_missing_nodes()
        self._extract_font_infos()
        self.verifier = PdfTreeVerifier(self)

        # Create SymlinkNodes for relationships between PDF objects that are not parent/child relationships.
        # (Do this last because it has the side effect of making a lot more nodes)
        for node in self.node_iterator():
            if not isinstance(node, SymlinkNode):
                node.symlink_non_tree_relationships()

        log.info(f"PDF walk completed in {time.perf_counter() - started_at:.2} seconds.")

    def close(self) -> None:
        """Close any open filehandles."""
        for attr in ['pdf_reader', 'pdf_filehandle']:
            if attr in vars(self):
                getattr(self, attr).close()

    def find_node_by_idnum(self, idnum: int) -> PdfTreeNode | None:
        """Find node with `idnum` in the tree. Return `None` if that node is not reachable from the root."""
        self._tree_nodes[idnum] = self._tree_nodes.get(idnum) or self.find_node_with_attr('idnum', idnum, True)
        return self._tree_nodes[idnum]

    def find_node_with_attr(self, attr: str, value: str | int, raise_if_multiple: bool = False) -> PdfTreeNode | None:
        """Find node with a property where you only expect one of those nodes to exist."""
        nodes = self.find_nodes_with_attr(attr, value)

        if len(nodes) == 0:
            return None
        elif len(nodes) > 1:
            msg = f"Found {len(nodes)} nodes with {attr}={value}, expected 1! {nodes}"

            if raise_if_multiple:
                raise PdfWalkError(msg)
            else:
                log.warning(msg)

        return nodes[0]

    def find_nodes_with_attr(self, attr_name: str, attr_value: str | int) -> list[PdfTreeNode]:
        """Find nodes in tree where 'attr_name' prop has the value 'attr_value'."""
        return [
            node for node in findall_by_attr(self.pdf_tree, name=attr_name, value=attr_value)
            if not isinstance(node, SymlinkNode)
        ]

    def is_in_tree(self, search_for_node: PdfTreeNode) -> bool:
        """Returns true if `search_for_node` is in the tree already."""
        return bool(self.find_node_by_idnum(search_for_node.idnum))

    def missing_node_ids(self) -> list[int]:
        """We expect to see all ordinals up to the number of nodes /Trailer claims exist as obj IDs."""
        all_object_ids = []

        # Try to get the list of object IDs with pdf-parser.py
        if PdfalyzerConfig.pdf_parser_path:
            if self.idnums_found_by_parser is None:
                try:
                    self.idnums_found_by_parser = PdfParserManager(self.pdf_path, PdfalyzerConfig.args.output_dir).object_ids
                    all_object_ids = self.idnums_found_by_parser
                    log.info(f"pdf-parser.py found {len(all_object_ids)} object IDs to verify...")

                    if self.num_nodes and self.num_nodes != (len(self.idnums_found_by_parser) + 1):
                        log.warning(f"pdf-parser.py found {len(self.idnums_found_by_parser)} objs but PDF reports {self.num_nodes}!")
                except Exception as e:
                    log.warning(f"Failed to extract object IDs with pdf-parser.py")
                    self.idnums_found_by_parser = []
            else:
                all_object_ids = self.idnums_found_by_parser

        # Fall back to all IDs between 0 and self.num_nodes
        if not all_object_ids:
            if self.num_nodes is None:
                log.error(f"no pdf-parser.py and {adobe_strings.SIZE} not found in PDF trailer; cannot verify all nodes are in tree")
                return []

            all_object_ids = [i for i in range(1, self.num_nodes)]

        return [i for i in all_object_ids if self.find_node_by_idnum(i) is None]

    def node_iterator(self) -> Iterator[PdfTreeNode]:
        """Iterate over nodes walking the tree from the top, grouped by distance from the root."""
        return LevelOrderIter(self.pdf_tree)

    def nodes_without_parents(self) -> list[PdfTreeNode]:
        """Return nodes that were encountered but have no parent set yet."""
        return [n for n in self.unplaced_encountered_nodes() if n.parent is None]

    def ref_and_obj_for_id(self, idnum: int) -> RefAndObj:
        """Build a new IndirectObject and PdfObject based on what's in the PDF."""
        ref = IndirectObject(idnum, self.max_generation, self.pdf_reader)

        try:
            obj = ref.get_object()
        except PdfReadError as e:
            if 'Invalid Elementary Object' in str(e):
                log.error(f"pypdf failed to find bad object: {e}")
                obj = None
            else:
                console.print_exception()
                log.error(str(e))
                raise e

        return RefAndObj(ref, obj)

    def stream_nodes(self) -> list[PdfTreeNode]:
        """List of actual nodes (not SymlinkNodes) containing streams sorted by PDF object ID"""
        stream_filter = lambda node: node.contains_stream() and not isinstance(node, SymlinkNode)  # noqa: E731
        return sorted(findall(self.pdf_tree, stream_filter), key=lambda r: r.idnum)

    def unplaced_encountered_nodes(self) -> list[PdfTreeNode]:
        """Nodes that were encountered by walk_node() but didn't end up in the tree."""
        return [node for id, node in self.nodes_encountered.items() if self.find_node_by_idnum(id) is None]

    def walk_node(self, node: PdfTreeNode) -> None:
        """Recursively walk the PDF's tree structure starting at a given node."""
        log.info(f'walk_node() called with {node}. Object dump:\n{highlighted_raw_pdf_obj_str(node.obj, node.label)}')
        nodes_to_walk_next = [self._add_relationship_to_pdf_tree(r) for r in node.references_to_other_nodes()]
        node.all_references_processed = True

        for next_node in [n for n in nodes_to_walk_next if not (n is None or n.all_references_processed)]:
            if not next_node.all_references_processed:
                self.walk_node(next_node)

            self.find_node_by_idnum(next_node.idnum)  # Trigger update of self._tree_nodes cache

    def _add_relationship_to_pdf_tree(self, relationship: PdfObjectRelationship) -> PdfTreeNode | None:
        """
        Place the `relationship` node in the tree. Returns an optional node that should be
        placed in the PDF node processing queue.
        """
        log.info(f'Assessing {relationship}...')
        was_seen_before = (relationship.to_obj.idnum in self.nodes_encountered)  # Must come before _build_or_find()
        from_node = relationship.from_node
        to_node = self._build_or_find_node(relationship.to_obj, relationship.address)
        self.max_generation = max([self.max_generation, relationship.to_obj.generation or 0])

        # If one is already a parent/child of the other there's nothing to do
        if to_node == from_node.parent or to_node in from_node.children:
            log.debug(f"  {from_node} and {to_node} are already parent/child")
            return None

        # NOTE: Many branches return None
        if relationship.is_parent or relationship.is_child:
            # If there's an explicit /Parent or /Kids relationship then we know the correct relationship
            log.debug(f"  Explicit parent/child link: {relationship}")

            if relationship.is_parent:
                from_node.set_parent(to_node)
            elif to_node.parent is not None:
                log.info(f"{relationship} fail: {to_node} parent is already {to_node.parent}")
            else:
                from_node.add_child(to_node)

            # Remove this to_node from inteterminacy now that it's got a child or parent
            if relationship.to_obj.idnum in self._indeterminate_ids:
                log.info(f"  Found {relationship} => {to_node} was marked indeterminate but now placed")
                self._indeterminate_ids.remove(relationship.to_obj.idnum)
        elif relationship.is_indeterminate or relationship.is_link or was_seen_before:
            # If the relationship is indeterminate or we've seen the PDF object before, add it as
            # a non-tree relationship for now. An attempt to place the node will be made at the end.
            to_node.add_non_tree_relationship(relationship)

            # If we already encountered 'to_node' then skip adding it to the queue of nodes to walk
            if was_seen_before:
                if relationship.to_obj.idnum not in self._indeterminate_ids and to_node.parent is None:
                    raise PdfWalkError(f"{relationship} - ref has no parent and is not indeterminate")
                else:
                    log_trace(f"  Already saw {relationship}; not scanning next")
                    return None
            elif relationship.is_indeterminate or (relationship.is_link and not self.is_in_tree(to_node)):
                # Indeterminate relationships need to wait until everything has been scanned to be placed
                log.info(f'  Indeterminate ref {relationship}')
                self._indeterminate_ids.add(to_node.idnum)
            elif relationship.is_link:
                # Link nodes like /Dest are usually just links between nodes
                log.debug(f"  Link ref {relationship}")
        else:
            # If no other conditions are met make from_node the parent of to_node
            from_node.add_child(to_node)

        # /StructElems in a /StructTreeRoot hierarchy sometimes have no /Type so we set it manually
        if to_node.type == adobe_strings.K and adobe_strings.STRUCT_TREE_ROOT in to_node.tree_address():
            to_node.pdf_object.type = adobe_strings.STRUCT_ELEM

        return to_node

    def _catalog_node(self) -> PdfTreeNode | None:
        return self.find_node_with_attr('type', adobe_strings.CATALOG)

    def _handle_fatal_error(self, msg: str, e: Exception) -> None:
        self.close()

        # Only exit if running in a 'pdfalyze some_file.pdf context', otherwise raise Exception.
        if is_pdfalyze_script:
            print_fatal_error_and_exit(msg, e)
        else:
            print_fatal_error(msg, e)
            raise e

    def _info_node(self) -> PdfTreeNode | None:
        return self.find_node_with_attr('type', adobe_strings.INFO)

    def _resolve_indeterminate_nodes(self) -> None:
        """Place indeterminate nodes in the tree."""
        indeterminate_nodes = [self.nodes_encountered[idnum] for idnum in self._indeterminate_ids]
        indeterminate_nodes_string = "\n   ".join([f"{node}" for node in indeterminate_nodes])
        log.info(f"Resolving {len(indeterminate_nodes)} indeterminate nodes: {indeterminate_nodes_string}")

        for node in indeterminate_nodes:
            if node.parent is not None:
                log.info(f"{node} marked indeterminate but has parent: {node.parent}")
                continue

            IndeterminateNode(node).place_node()

    def _resolve_missing_nodes(self) -> None:
        """Make a best effort to place nodes we have so far failed to get into the tree hierarchy."""
        missing_node_ids = self.missing_node_ids()

        if len(missing_node_ids) > MISSING_NODE_WARN_THRESHOLD:
            log.warning(f"Found {len(missing_node_ids)} missing node IDs. This could take a while to sort out...")

        # Place /ObjStm at root if no other location found.
        for idnum in missing_node_ids:
            ref_and_obj = self.ref_and_obj_for_id(idnum)
            ref = ref_and_obj.ref
            obj = ref_and_obj.obj
            # Make sure we didn't already fix this node up in the course of other repairs
            node = self.find_node_by_idnum(ref.idnum)

            if not isinstance(obj, DictionaryObject) or (node is not None and node.parent):
                continue

            # Handle special Linearization info nodes
            if obj.get(adobe_strings.TYPE) is None and '/Linearized' in obj:
                log.warning(f"Placing special /Linearized node {describe_obj(ref_and_obj)} as child of root")
                self.pdf_tree.add_child(self._build_or_find_node(ref, '/Linearized'))
            elif obj.get(adobe_strings.TYPE) == adobe_strings.OBJ_STM:
                log.warning(f"Forcing homeless {describe_obj(ref_and_obj)} to appear as child of root node")
                self.pdf_tree.add_child(self._build_or_find_node(ref, adobe_strings.OBJ_STM))
            elif obj.get(adobe_strings.TYPE) == adobe_strings.XOBJECT and obj.get(adobe_strings.SUBTYPE) == '/Form':
                if (form := self.find_node_with_attr('type', adobe_strings.ACRO_FORM)):
                    log.warning(f"Forcing homeless {describe_obj(ref_and_obj)} to be child of {adobe_strings.ACRO_FORM}")
                    form.add_child(self._build_or_find_node(ref, adobe_strings.XOBJECT))

        # Force /Pages to be children of /Catalog
        for node in self.nodes_without_parents():
            if node.type == adobe_strings.PAGES and (catalog_node := self._catalog_node()):
                log.warning(f"Forcing orphaned {adobe_strings.PAGES} node {node} to be child of {catalog_node}")
                node.set_parent(catalog_node)

    def _extract_font_infos(self) -> None:
        """Extract information about fonts in the tree and place it in `self.font_infos`."""
        for node in self.node_iterator():
            if not (isinstance(node.obj, dict) and adobe_strings.RESOURCES in node.obj):
                continue

            log.debug(f"Extracting fonts from node with '{adobe_strings.RESOURCES}' key: {node}...")
            known_font_ids = [fi.idnum for fi in self.font_infos]

            try:
                self.font_infos += [
                    fi for fi in FontInfo.extract_font_infos(node.obj)
                    if fi.idnum not in known_font_ids
                ]
            except Exception as e:
                self.font_info_extraction_error = e
                console.line()
                log.warning(f"Failed to extract font information from node: {node} (error: {e})")
                console.line()

        self.font_infos = sorted(self.font_infos, key=lambda fi: fi.idnum)

    def _build_or_find_node(self, relationship: IndirectObject, relationship_key: str) -> PdfTreeNode:
        """If node in self.nodes_encountered already then return it, otherwise build a node and store it."""
        if relationship.idnum in self.nodes_encountered:
            return self.nodes_encountered[relationship.idnum]

        log_trace(f"Building node for {relationship}")
        new_node = PdfTreeNode.from_reference(relationship, relationship_key)
        self.nodes_encountered[relationship.idnum] = new_node
        return new_node

    def _print_nodes_encountered(self) -> None:
        """Debug method that displays which nodes have already been walked."""
        for i in sorted(self.nodes_encountered.keys()):
            console.print(f'{i}: {self.nodes_encountered[i]}')
