"""
Verify that the PDF tree is complete/contains all the nodes in the PDF file.
"""
from dataclasses import dataclass, field
from types import NoneType
from typing import Callable, cast

from pypdf import PdfReader
from pypdf.errors import PdfReadError
from pypdf.generic import (ArrayObject, BooleanObject, DictionaryObject, IndirectObject, NameObject, NullObject,
     NumberObject, PdfObject, StreamObject)
from rich.markup import escape
from yaralyzer.util.logging import log

from pdfalyzer.decorators.document_model_printer import highlighted_raw_pdf_obj_str
from pdfalyzer.decorators.pdf_tree_node import PdfTreeNode
from pdfalyzer.helpers.pdf_object_helper import describe_obj
from pdfalyzer.util.adobe_strings import *

NUM_PREVIEW_BYTES = 1_024
OK_UNPLACED_TYPES = (BooleanObject, NameObject, NoneType, NullObject, NumberObject)


@dataclass
class PdfTreeVerifier:
    """
    Class to verify that the PDF tree is complete/contains all the nodes in the PDF file.

    Attributes:
        pdfalyzer (Pdfalyzer): The Pdfalyzer instance being verified
    """
    pdfalyzer: 'Pdfalyzer'

    def log_missing_node_warnings(self) -> None:
        print('')
        unplaced_encountered_nodes = self.pdfalyzer.unplaced_encountered_nodes()

        if self.pdfalyzer.max_generation > 0:
            log.warning(f"Verification doesn't check revisions (this PDF's generation is {self.pdfalyzer.max_generation})\n")

        if len(unplaced_encountered_nodes) > 0:
            msg = f"Some nodes were traversed but never placed: {escape(str(unplaced_encountered_nodes))}\n\n" + \
                   "For link nodes like /First, /Next, /Prev, and /Last this might be no big deal - depends " + \
                   "on the PDF. But for other node typtes this could indicate missing data in the tree.\n"
            log.warning(msg)

        self._log_all_unplaced_nodes()
        missing_node_ids = self.pdfalyzer.missing_node_ids()
        notable_missing_node_ids = self.notable_missing_node_ids()
        indeterminate_missing_node_ids = [id for id in missing_node_ids if id in self.pdfalyzer._indeterminate_ids]
        all_missing_nodes_msg = f"{len(missing_node_ids)} missing node ids: {missing_node_ids}\n"

        if notable_missing_node_ids:
            log.warning(f"Found {len(notable_missing_node_ids)} important missing node IDs: {notable_missing_node_ids}")

            if missing_node_ids != notable_missing_node_ids:
                log.warning(f"All of the {all_missing_nodes_msg}")
        elif missing_node_ids:
            log.warning(f"Probably unimportant {all_missing_nodes_msg}")

        if indeterminate_missing_node_ids:
            log.warning(f"These missing IDs were marked as indeterminate when treewalking:\n{indeterminate_missing_node_ids}\n")

        nodes_without_parents = self.pdfalyzer.nodes_without_parents()
        node_ids_without_parents = [n.idnum for n in nodes_without_parents]

        if node_ids_without_parents:
            node_id_to_child_count = {n.idnum: f"has {len(n.children)} children" for n in nodes_without_parents}
            log.warning(f"These node IDs were parsed but have no parent:\n{node_id_to_child_count}\n")
        elif notable_missing_node_ids:
            log.warning(f"None of the missing nodes were enountered while walking the tree.", extra={"highlighter": None})

    def notable_missing_node_ids(self) -> list[int]:
        """Missing idnums that aren't NullObject, NumberObject, etc."""
        notable_ids = []

        for idnum in self.pdfalyzer.missing_node_ids():
            _ref, obj = self.pdfalyzer.ref_and_obj_for_id(idnum)
            msg = f"Missing node {idnum} {describe_obj(obj)}"

            if isinstance(obj, OK_UNPLACED_TYPES):
                log.info(f"{msg} but it's an acceptable type (value={obj})")
            elif isinstance(obj, (ArrayObject, DictionaryObject)) and len(obj) == 0:
                if isinstance(obj, StreamObject) and len(obj.get_data()) > 0:
                    notable_ids.append(idnum)
                else:
                    log.info(f"{msg} but it's empty, so it's ok")
            else:
                notable_ids.append(idnum)

        return notable_ids

    def was_successful(self):
        """Return True if no unplaced nodes or missing node IDs."""
        return (len(self.pdfalyzer.unplaced_encountered_nodes()) + len(self.notable_missing_node_ids())) == 0

    def _log_all_unplaced_nodes(self) -> None:
        """Log warning for each unplaced node."""
        for idnum in self.pdfalyzer.missing_node_ids():
            ref, obj = self.pdfalyzer.ref_and_obj_for_id(idnum)

            if obj is None:
                log.warning(f"No object with ID {idnum} seems to exist in the PDF...")
                continue
            elif isinstance(obj, OK_UNPLACED_TYPES):
                log.info(f"Obj {idnum} is a {describe_obj(obj)} w/value {obj}; if relationship by /Length etc. this is a nonissue but maybe worth doublechecking")  # noqa: E501
                continue
            elif not isinstance(obj, DictionaryObject):
                self._log_failure(idnum, obj, "isn't a dict, cannot determine if it should be in tree")
                continue
            elif TYPE not in obj:
                self._log_failure(idnum, obj, f"has no {TYPE}")
                continue

            self._log_failure(idnum, obj)

    def _log_failure(self, idnum: int, obj: PdfObject, msg: str = '', log_fxn: Callable | None = None) -> None:
        s = f"{obj.get(TYPE)} " if isinstance(obj, DictionaryObject) and TYPE in obj else ''
        s += f"Obj {idnum} ({type(obj).__name__}) failed to be placed in the PDF tree"
        s += f" ({msg})." if msg else '.'

        if len([k for k in obj]) == 0:
            s += f" but it's an empty object so not particularly concerning. "
        else:
            s += f" Could be a bad PDF or an error in pdfalyzer; here's the contents for you to assess:\n\n"
            s += highlighted_raw_pdf_obj_str(obj, header=f"Unplaced PdfObject {idnum}")

        if isinstance(obj, StreamObject):
            data = obj.get_data()
            s += "\nIt has an embedded binary stream"

            if len(data) == 0:
                s+= " but the stream has 0 bytes in it."
            else:
                s += f" of {len(data):,} bytes"
                s += f", here's a preview of the first {NUM_PREVIEW_BYTES:,} bytes" if len(data) > NUM_PREVIEW_BYTES else ''
                s += f":\n{data[:NUM_PREVIEW_BYTES]}"

        (log_fxn or log.warning)(f"{s}\n")

        # if isinstance(obj, StreamObject):
        #     try:
        #         (log_fxn or log.warning)(f"{obj.get_data().decode()}")
        #     except Exception as e:
        #         log.warning(f"Failed to decode obj stream data to str")
