"""
Verify that the PDF tree is complete/contains all the nodes in the PDF file.
"""
from dataclasses import dataclass, field
from types import NoneType
from typing import Callable, cast

from pypdf import PdfReader
from pypdf.errors import PdfReadError
from pypdf.generic import (BooleanObject, DictionaryObject, IndirectObject, NameObject, NullObject,
     NumberObject, PdfObject, StreamObject)
from rich.markup import escape
from yaralyzer.output.rich_console import console
from yaralyzer.util.logging import log

from pdfalyzer.decorators.document_model_printer import highlighted_raw_pdf_obj_str
from pdfalyzer.decorators.pdf_tree_node import PdfTreeNode
from pdfalyzer.util.adobe_strings import *

OK_UNPLACED_TYPES = (BooleanObject, NameObject, NoneType, NullObject, NumberObject)


@dataclass
class PdfTreeVerifier:
    """
    Class to verify that the PDF tree is complete/contains all the nodes in the PDF file.

    Attributes:
        pdfalyzer (Pdfalyzer): The Pdfalyzer instance being verified
        unplaced_encountered_nodes (list[PdfTreeNode]): Nodes encounted by walk_node() that aren't in the tree
    """
    pdfalyzer: 'Pdfalyzer'
    unplaced_encountered_nodes: list[PdfTreeNode] = field(init=False)

    def __post_init__(self):
        self.unplaced_encountered_nodes = self.pdfalyzer.unplaced_encountered_nodes()
        self._verify_unencountered_are_untraversable()

    def log_final_warnings(self) -> None:
        print('')

        if self.pdfalyzer.max_generation > 0:
            log.warning(f"Verification doesn't check revisions (this PDF's generation is {self.pdfalyzer.max_generation})\n")

        if len(self.unplaced_encountered_nodes) > 0:
            msg = f"Some nodes were traversed but never placed: {escape(str(self.unplaced_encountered_nodes))}\n\n" + \
                   "For link nodes like /First, /Next, /Prev, and /Last this might be no big deal - depends " + \
                   "on the PDF. But for other node typtes this could indicate missing data in the tree.\n"
            log.warning(msg)

        log.warning(f"All missing node ids: {self.pdfalyzer.missing_node_ids()}\n")
        log.warning(f"Important missing node IDs: {self.notable_missing_node_ids()}")

        for idnum in self.pdfalyzer.missing_node_ids():
            _ref, obj = self._ref_and_obj_for_id(idnum)
            log.warning(f"Missing node ID {idnum} ({type(obj).__name__})")

        log.warning(f"Unplaced nodes: {self.unplaced_encountered_nodes}\n")

    def notable_missing_node_ids(self) -> list[int]:
        """Missing idnums that aren't NullObject, NumberObject, etc."""
        notable_ids = []

        for idnum in self.pdfalyzer.missing_node_ids():
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

        return (ref, obj)

    def _verify_unencountered_are_untraversable(self) -> None:
        """
        Make sure any PDF object IDs we can't find in tree are /ObjStm or /Xref nodes and
        make a final attempt to place a few select kinds of nodes.
        """
        for idnum in self.pdfalyzer.missing_node_ids():
            ref, obj = self._ref_and_obj_for_id(idnum)

            if obj is None:
                log.error(f"Couldn't verify elementary obj with id {idnum} is properly in tree")
                continue
            elif isinstance(obj, (NumberObject, NameObject)):
                log.info(f"Obj {idnum} is a {type(obj)} w/value {obj}; if relationshipd by /Length etc. this is a nonissue but maybe worth doublechecking")  # noqa: E501
                continue
            elif not isinstance(obj, dict):
                self._log_failure(idnum, obj, "isn't a dict, cannot determine if it should be in tree", log.error)
                continue
            elif TYPE not in obj:
                self._log_failure(idnum, obj, f"has no {TYPE}")
                continue

            obj_type = obj[TYPE]

            if obj_type == OBJ_STM:
                self._log_failure(idnum, obj, f"placing at root bc it's an {OBJ_STM}", log.info)
                self.pdfalyzer.pdf_tree.add_child(self.pdfalyzer._build_or_find_node(ref, OBJ_STM))
                continue
                # # Didier Stevens parses /ObjStm as a synthetic PDF here: https://github.com/DidierStevens/DidierStevensSuite/blob/master/pdf-parser.py#L1605
                # if idnum != 2:
                #     continue

                # from io import BytesIO
                # stream_data = obj.get_data()
                # stream_offset = obj.get('/First') or 0
                # offset_stream_data = stream_data[stream_offset:]
                # log.warning(f"Offset stream: {offset_stream_data[0:100]}")
                # stream = BytesIO(offset_stream_data)
                # import pdb;pdb.set_trace()
                # p = PdfReader(stream)
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
                self._log_failure(idnum, obj)

    def _log_failure(self, idnum: int, obj: PdfObject, msg: str = '', log_fxn: Callable | None = None) -> None:
        s = f"{obj.get(TYPE)} " if isinstance(obj, DictionaryObject) and TYPE in obj else ''
        s += f"Obj {idnum} ({type(obj).__name__}) is not in tree"
        s += f" ({msg})." if msg else '.'
        s += f" Either a loose node w/no data or an error in pdfalyzer"

        if len([k for k in obj]) == 0:
            s += f" but it's an empty object so not particularly concerning. "
        else:
            s += f" here's the contents for you to assess:\n\n"
            s += highlighted_raw_pdf_obj_str(obj, header=f"unplaced object {idnum}")

        s += f"It has an embedded binary stream:\n{obj.get_data()}" if isinstance(obj, StreamObject) else ''
        (log_fxn or log.warning)(f"{s}\n")

        # if isinstance(obj, StreamObject):
        #     try:
        #         (log_fxn or log.warning)(f"{obj.get_data().decode()}")
        #     except Exception as e:
        #         log.warning(f"Failed to decode obj stream data to str")
