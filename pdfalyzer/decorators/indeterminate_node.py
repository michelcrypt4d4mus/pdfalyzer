"""
Some nodes cannot be placed until we have walked the rest of the tree. For instance
if we encounter a /Page that relationships /Resources we need to know if there's a
/Pages parent of the /Page before committing to a tree structure.

This class handles choosing among the candidates for a given PDF object's parent node
(AKA "figuring out where to place the node in the PDF object tree").
"""
from typing import Callable, List, Optional

from rich.markup import escape
from yaralyzer.helpers.string_helper import comma_join
from yaralyzer.util.logging import log

from pdfalyzer.decorators.pdf_tree_node import PdfTreeNode
from pdfalyzer.helpers.string_helper import all_strings_are_same_ignoring_numbers, has_a_common_substring
from pdfalyzer.util.adobe_strings import *


class IndeterminateNode:
    def __init__(self, node: PdfTreeNode) -> None:
        self.node = node

    def place_node(self) -> None:
        """Attempt to find the appropriate parent/child relationships for this node."""
        log.debug(f"Attempting to resolve indeterminate node: {self.node}")

        if self._check_for_common_ancestor():
            return
        elif self._check_single_relation_rules():
            return

        # At this point we will choose the relationship with the most descendants as the parent.
        # We will display a warning if we can't find any reason better than that to choose the parent.
        parent = self.find_node_with_most_descendants()
        parent_str = escape(str(parent))

        # Any if/else branch that doesn't return or raise will decide parent to be the node w/most descendants
        if self._has_only_similar_relationships():
            log.info(f"  Fuzzy match addresses or labels; placing under node w/most descendants: {parent_str}")
        elif self._make_parent_if_one_remains(lambda r: r.from_node.type in PAGE_AND_PAGES):
            log.info("  Found a single /Page or /Pages relationship to make parent")
            return
        elif self.node.type == COLOR_SPACE:
            log.info(f"  Color space node found; placing under node w/most descendants: {parent_str}")
        elif set(self.node.unique_labels_of_referring_nodes()) == set(PAGE_AND_PAGES):
            # Handle an edge case seen in the wild involving a PDF that doesn't conform to the PDF spec
            # in a particular way.
            log.warning(f"  {self.node} seems to be a loose {PAGE}. Linking to first {PAGES}")
            pages_nodes = [n for n in self.node.nodes_with_here_references() if self.node.type == PAGES]
            self.node.set_parent(self.find_node_with_most_descendants(pages_nodes))
            return
        else:
            log.warning(f"  {self.node} parent {parent_str} chosen based on descendant count only")
            self.node.log_non_tree_relationships()

        self.node.set_parent(parent)

    def find_node_with_most_descendants(self, list_of_nodes: List[PdfTreeNode] = None) -> PdfTreeNode:
        """Find node with a reference to this one that has the most descendants"""
        list_of_nodes = list_of_nodes or [r.from_node for r in self.node.non_tree_relationships]
        max_descendants = max([node.descendants_count() for node in list_of_nodes])
        return find_node_with_lowest_id([n for n in list_of_nodes if n.descendants_count() == max_descendants])

    def _has_only_similar_relationships(self) -> bool:
        """
        Returns True if all the nodes w/references to this one have the same type or if all the
        reference_keys that point to this node are the same.
        """
        unique_refferer_labels = self.node.unique_labels_of_referring_nodes()
        unique_addresses = self.node.unique_addresses()

        # Check addresses and referring node labels to see if they are all the same
        reference_keys_or_nodes_are_same = any([
            all_strings_are_same_ignoring_numbers(_list) or has_a_common_substring(_list)
            for _list in [unique_addresses, unique_refferer_labels]
        ])

        return reference_keys_or_nodes_are_same

    def _check_for_common_ancestor(self) -> bool:
        common_ancestor = self._find_common_ancestor_among_nodes(self.node.nodes_with_here_references())

        if common_ancestor is not None:
            log.info(f"  Found common ancestor: {common_ancestor}")
            self.node.set_parent(common_ancestor)
            return True
        else:
            return False

    # TODO could be static method
    def _find_common_ancestor_among_nodes(self, nodes: List[PdfTreeNode]) -> Optional[PdfTreeNode]:
        """If any of 'nodes' is a common ancestor of the rest of the 'nodes', return it."""
        for possible_ancestor in nodes:
            log.debug(f"  Checking possible common ancestor: {possible_ancestor}")
            other_nodes = [n for n in nodes if n != possible_ancestor]

            # Look for a common ancestor; if there is one choose it as the parent.
            if all(possible_ancestor in node.ancestors for node in other_nodes):
                other_nodes_str = comma_join([str(node) for node in other_nodes])
                log.info(f"{possible_ancestor} is the common ancestor of {other_nodes_str}")
                return possible_ancestor

    def _check_single_relation_rules(self) -> bool:
        """Check various ways of narrowing down the list of potential parents to one node."""
        if self._make_parent_if_one_remains(lambda r: r.reference_key in [K, KIDS]):
            log.info("  Found single explicit /K or /Kids ref")
        elif self._make_parent_if_one_remains(lambda r: r.from_node.type not in NON_TREE_KEYS):
            log.info("  Found single determinate relationship")
        else:
            return False

        return True

    def _make_parent_if_one_remains(self, is_possible_parent: Callable) -> bool:
        """Relationships are filtered w/is_possible_parent(); if there's only one possibility it's made the parent."""
        remaining_relationships = [r for r in self.node.non_tree_relationships if is_possible_parent(r)]

        if len(remaining_relationships) == 1:
            log.info(f"  Single remaining relationship {remaining_relationships[0]}; making it the parent")
            self.node.set_parent(remaining_relationships[0].from_node)
            return True
        else:
            return False


def find_node_with_lowest_id(list_of_nodes: List[PdfTreeNode]) -> PdfTreeNode:
    """Find node in list_of_nodes_with_lowest ID."""
    lowest_idnum = min([n.idnum for n in list_of_nodes])
    return next(n for n in list_of_nodes if n.idnum == lowest_idnum)
