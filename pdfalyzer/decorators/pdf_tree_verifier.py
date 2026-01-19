"""
Verify that the PDF tree is complete/contains all the nodes in the PDF file.
"""
from dataclasses import dataclass, field
from types import NoneType

from pypdf.errors import PdfReadError
from pypdf.generic import BooleanObject, IndirectObject, NameObject, NullObject, NumberObject, PdfObject
from rich.markup import escape
from yaralyzer.output.rich_console import console
from yaralyzer.util.logging import log

from pdfalyzer.decorators.pdf_tree_node import PdfTreeNode
from pdfalyzer.util.adobe_strings import *

OK_UNPLACED_TYPES = (BooleanObject, NameObject, NoneType, NullObject, NumberObject)


@dataclass
class PdfTreeVerifier:
    """Class to verify that the PDF tree is complete/contains all the nodes in the PDF file."""
    pdfalyzer: 'Pdfalyzer'
    unplaced_encountered_nodes: list[PdfTreeNode] = field(init=False)

    def __post_init__(self):
        self.unplaced_encountered_nodes = [
            node for idnum, node in self.pdfalyzer.nodes_encountered.items()
            if self.pdfalyzer.find_node_by_idnum(idnum) is None
        ]

        if len(self.unplaced_encountered_nodes) > 0:
            msg = f"Nodes were traversed but never placed: {escape(str(self.unplaced_encountered_nodes))}\n\n" + \
                   "For link nodes like /First, /Next, /Prev, and /Last this might be no big deal - depends " + \
                   "on the PDF. But for other node typtes this could indicate missing data in the tree."
            log.warning(msg)

        self._verify_unencountered_are_untraversable()

    def log_final_warnings(self) -> None:
        print('')
        log.warning(f"All missing node ids: {self.missing_node_ids()}\n")
        log.warning(f"Important missing node IDs: {self.notable_missing_node_ids()}")

        for idnum in self.missing_node_ids():
            ref, obj = self._ref_and_obj_for_id(idnum)
            log.warning(f"Missing node ID {idnum} ({type(obj).__name__})")

        log.warning(f"Unplaced nodes: {self.unplaced_encountered_nodes}\n")

    def missing_node_ids(self) -> list[int]:
        """We expect to see all ordinals up to the number of nodes /Trailer claims exist as obj IDs."""
        return [
            i for i in range(1, self.pdfalyzer.pdf_size)
            if self.pdfalyzer.find_node_by_idnum(i) is None
        ]

    def notable_missing_node_ids(self) -> list[int]:
        """Missing idnums that aren't NullObject, NumberObject, etc."""
        notable_ids = []

        for idnum in self.missing_node_ids():
            _ref, obj = self._ref_and_obj_for_id(idnum)

            if isinstance(obj, OK_UNPLACED_TYPES):
                log.info(f"Missing node {idnum} but it's an acceptable type ({type(obj).__name__}, value={obj}")
            else:
                notable_ids.append(idnum)

        return notable_ids

    def was_successful(self):
        """Return True if no unplaced nodes or missing node IDs."""
        return (len(self.unplaced_encountered_nodes) + len(self.notable_missing_node_ids())) == 0

    def _ref_and_obj_for_id(self, idnum: int) -> tuple[IndirectObject, PdfObject | None]:
        ref = IndirectObject(idnum, self.pdfalyzer.max_generation, self.pdfalyzer.pdf_reader)
        obj = None

        try:
            obj = ref.get_object()
        except PdfReadError as e:
            if 'Invalid Elementary Object' in str(e):
                log.warning(f"Bad object: {e}")
            else:
                console.print_exception()
                log.error(str(e))
                raise e

        return (ref, obj)

    def _verify_unencountered_are_untraversable(self) -> None:
        """
        Make sure any PDF object IDs we can't find in tree are /ObjStm or /Xref nodes and
        make a final attempt to place a few select kinds of nodes.
        """
        if self.pdfalyzer.pdf_size is None:
            log.error(f"{SIZE} not found in PDF trailer; cannot verify all nodes are in tree")
            return

        if self.pdfalyzer.max_generation > 0:
            log.warning(f"Verification doesn't check revisions but this PDF's generation is {self.pdfalyzer.max_generation}")

        for idnum in self.missing_node_ids():
            ref, obj = self._ref_and_obj_for_id(idnum)

            if obj is None:
                log.error(f"Couldn't verify elementary obj with id {idnum} is properly in tree")
                continue
            elif isinstance(obj, (NumberObject, NameObject)):
                log.info(f"Obj {idnum} is a {type(obj)} w/value {obj}; if relationshipd by /Length etc. this is a nonissue but maybe worth doublechecking")  # noqa: E501
                continue
            elif not isinstance(obj, dict):
                log.error(f"Obj {idnum} ({obj}) of type {type(obj)} isn't dict, cannot determine if it should be in tree")  # noqa: E501
                continue
            elif TYPE not in obj:
                msg = f"Obj {idnum} has no {TYPE} and is not in tree. Either a loose node w/no data or an error in pdfalyzer."  # noqa: E501
                msg += f"\nHere's the contents for you to assess:\n{obj}"
                log.warning(msg)
                continue

            obj_type = obj[TYPE]

            if obj_type == OBJECT_STREAM:
                log.debug(f"Object with id {idnum} not found in tree because it's an {OBJECT_STREAM}")
            elif obj[TYPE] == XREF:
                placeable = XREF_STREAM in self.pdfalyzer.pdf_reader.trailer

                for k, v in self.pdfalyzer.pdf_reader.trailer.items():
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
                    self.pdfalyzer.pdf_tree.add_child(self.pdfalyzer._build_or_find_node(ref, XREF_STREAM))
            else:
                log.warning(f"{XREF} Obj {idnum} not found in tree!")
