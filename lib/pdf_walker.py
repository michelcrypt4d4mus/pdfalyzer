"""
Walks the PDF objects, wrapping each in a PdfTreeNode and putting them into a tree
managed by the anytree library. Once the PDF is parsed this class manages things like
searching the tree and printing out information.
"""
from collections import defaultdict
from os.path import basename

from anytree import LevelOrderIter, RenderTree, SymlinkNode
from anytree.render import DoubleStyle
from anytree.search import findall_by_attr
from PyPDF2 import PdfReader
from PyPDF2.generic import IndirectObject
from rich.panel import Panel
from rich.text import Text

from lib.decorators.document_model_printer import print_with_header
from lib.decorators.pdf_tree_node import PdfTreeNode
from lib.font_info import FontInfo
from lib.util.adobe_strings import (COLOR_SPACE, DEST, EXT_G_STATE, FONT, K, KIDS, NON_TREE_REFERENCES, NUMS,
     OPEN_ACTION, P, PARENT, RESOURCES, SIZE, STRUCT_ELEM, TRAILER, UNLABELED, XOBJECT)
from lib.util.exceptions import PdfWalkError
from lib.util.logging import log
from lib.util.string_utils import console, get_symlink_representation, pp, print_section_header


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


class PdfWalker:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_basename = basename(pdf_path)
        pdf_file = open(pdf_path, 'rb')  # Filehandle must be left open for PyPDF2 to perform seeks
        self.pdf = PdfReader(pdf_file)
        # Initialize tracking variables
        self.indeterminate_ids = set()  # See INDETERMINATE_REFERENCES comment
        self.traversed_nodes = {}
        self.font_infos = []
        self.walk_pdf()

    def walk_pdf(self):
        """
        PDFs are read trailer first so trailer is the root of the tree.
        We build the rest by recursively following references we find in nodes we encounter.
        """
        trailer = self.pdf.trailer
        # Technically the trailer has no ID in the PDF but we set it to the number of objects for convenience
        self.pdf_tree = PdfTreeNode(trailer, TRAILER, trailer.get(SIZE, 100000000))
        self.traversed_nodes[self.pdf_tree.idnum] = self.pdf_tree
        self.walk_node(self.pdf_tree)
        self._resolve_indeterminate_nodes()  # After scanning all the objects we place nodes whose position was uncertain
        self._extract_font_infos()
        self._verify_all_traversed_nodes_are_in_tree()
        self._symlink_other_relationships()  # Create symlinks for non parent/child relationships between nodes
        log.info(f"Walk complete.")

    def walk_node(self, node: PdfTreeNode):
        """Recursively walk the PDF's tree structure starting at a given node"""
        log.info(f'walk_node() called with {node}. Object dump:\n{print_with_header(node.obj, node.label)}')
        self._ensure_safe_to_walk(node)
        nodes_to_walk_next = []

        # Build PdfTreeNode objects for refs in :node; figure out what refs should be walked next
        for key, value in node.references().items():
            if isinstance(value, IndirectObject):
                nodes_to_walk_next += self._process_reference(node, key, key, value)
            elif isinstance(value, list):
                for i, reference in enumerate(value):
                    # Lists can have a mix of values and IndirectObject refs so we skip the non-refs
                    if not isinstance(reference, IndirectObject):
                        continue

                    # Array element references get an index, e.g. 'Kids[0]', 'Kids[1]', etc.
                    nodes_to_walk_next += self._process_reference(node, key, f'{key}[{i}]', reference)
            elif isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if not isinstance(subvalue, IndirectObject):
                        continue

                    # Dict element references get brackets, e.g. 'Font[/F1]', 'Font[/F2]', etc.
                    nodes_to_walk_next += self._process_reference(node, key, f'{key}[{subkey}]', subvalue)
            elif isinstance(value, (IndirectObject, list, dict)):
                raise PdfWalkError(f"Failed to process {node} ref {key} to {reference} ({reference.get_object()}")

        for next_node in nodes_to_walk_next:
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

    def print_tree(self):
        print_section_header(f'Simple tree view of {self.pdf_basename}')

        for pre, _fill, node in RenderTree(self.pdf_tree, style=DoubleStyle):
            if isinstance(node, SymlinkNode):
                symlink_rep = get_symlink_representation(node.parent, node)
                console.print(pre + f"[{symlink_rep.style}]{symlink_rep.text}[/{symlink_rep.style}]")
            else:
                console.print(Text(pre) + node.__str_with_color__())

        console.print("\n\n")

    def print_rich_table_tree(self) -> None:
        print_section_header(f'Rich tree view of {self.pdf_basename}')
        console.print(self.pdf_tree.generate_rich_tree())

    def print_summary(self) -> None:
        print_section_header(f'PDF Node Summary for {self.pdf_basename}')
        console.print_json(data=self._analyze_tree(), sort_keys=True)

    def print_font_info(self) -> None:
        print_section_header(f'{len(self.font_infos)} fonts found in {self.pdf_basename}')

        for font_info in self.font_infos:
            font_info.print_summary()

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

    def print_traversed_nodes(self) -> None:
        """Debug method that displays which nodes have already been walked"""
        for i in sorted(self.traversed_nodes.keys()):
            console.print(f'{i}: {self.traversed_nodes[i]}')

    def _process_reference(self, node: PdfTreeNode, key: str, k: str, reference: IndirectObject) -> [PdfTreeNode]:
        """Place the referenced node in the tree. Returns a list of nodes to walk next."""
        seen_before = (reference.idnum in self.traversed_nodes)
        referenced_node = self._build_or_find_node(reference, k)
        reference_log_string = f"{node} reference at {k} to {referenced_node}"
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
                log.info(f"  Found refefence {k} => {node} of previously indeterminate node {referenced_node}")
                self.indeterminate_ids.remove(reference.idnum)

            if not seen_before:
                references_to_return = [referenced_node]

        # Non tree references are not children or parents.
        # Checking startswith(NUMS) is a hack that probably will not cover all cases with /StructElem
        elif key in NON_TREE_REFERENCES or node.label.startswith(NUMS) :
            log.debug(f"{reference_log_string} is a non tree reference.")
            referenced_node.add_relationship(node, k)

            if not self.find_node_by_idnum(referenced_node.idnum):
                references_to_return = [referenced_node]

        # Indeterminate references need to wait until everything has been scanned to be placed
        elif key in INDETERMINATE_REFERENCES:
            log.warning(f'  Indeterminate {reference_log_string}')
            referenced_node.add_relationship(node, k)
            self.indeterminate_ids.add(referenced_node.idnum)
            return [referenced_node]

        # If we've seen the node before it should have a parent or be indeterminate
        elif seen_before:
            if reference.idnum not in self.indeterminate_ids and referenced_node.parent is None:
                raise PdfWalkError(f"{reference_log_string} - ref has no parent and is not indeterminate")

            referenced_node.add_relationship(node, k)

        # If no other conditions are met, add the reference as a child
        else:
            node.add_child(referenced_node)
            references_to_return = [referenced_node]

        return references_to_return

    def _symlink_other_relationships(self):
        """Create SymlinkNodes for relationships between PDF objects that are not parent/child relationships"""
        for node in LevelOrderIter(self.pdf_tree):
            if node.other_relationnship_count() == 0 or isinstance(node, SymlinkNode):
                continue

            log.info(f"Symlinking {node}'s {node.other_relationnship_count()} other relationships...")

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
        log.info(f"Resolving indeterminate nodes\n{indeterminate_nodes_string}")

        for idnum in self.indeterminate_ids:
            if self.find_node_by_idnum(idnum):
                log.warning(f"{idnum} is already in tree...")
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
                node.other_relationships.remove(lowest_id_relationship)
                continue

            self.print_tree()
            log.fatal("Dumped tree status for debugging.")
            node.print_other_relationships()
            raise PdfWalkError(f"Cannot place {node}")

    def _extract_font_infos(self) -> None:
        """Extract information about fonts in the tree and place it in self.font_infos"""
        for resource_node in [node for node in findall_by_attr(self.pdf_tree, name='label', value=RESOURCES)]:
            log.debug(f"Extracting fonts from {resource_node}...")
            known_font_ids = [fi.idnum for fi in self.font_infos]

            self.font_infos += [
                fi for fi in FontInfo.extract_font_infos(resource_node.parent.obj)
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
                resources_node.other_relationships.remove(relationship)
                return

        log.error(f"Failed to place {resources_node}. {RESOURCES} relationship dump:")
        resources_node.print_other_relationships()
        raise PdfWalkError(f'Failed to place {resources_node}')

    def _build_or_find_node(self, reference: IndirectObject, reference_key: str) -> PdfTreeNode:
        """If node exists in self.traversed_nodes return it, otherwise build a node"""
        if reference.idnum in self.traversed_nodes:
            return self.traversed_nodes[reference.idnum]

        # TODO: known_to_parent_as should not be passed for non-child relationships (as it stands it is
        #       corrected later when the true parent is found)
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

            if isinstance(node, dict):
                for k in node.obj.keys():
                    keys_encountered[k] += 1

        return {
            'node_count': node_count,
            'pdf_object_types': pdf_object_types,
            'node_labels': node_labels,
            'keys_encountered': keys_encountered
        }

    def _verify_all_traversed_nodes_are_in_tree(self) -> None:
        """Make sure every node we can see is reachable from the root of the tree"""
        missing_nodes = [node for idnum, node in self.traversed_nodes.items() if self.find_node_by_idnum(idnum) is None]

        if len(missing_nodes) > 0:
            msg = f"Nodes were traversed but never placed: {missing_nodes}"
            console.print(msg)
            raise PdfWalkError(msg)
