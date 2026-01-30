"""
Verify that the PDF tree is complete/contains all the nodes in the PDF file.
"""
from dataclasses import dataclass, field
from types import NoneType

from pypdf.generic import (ArrayObject, BooleanObject, DictionaryObject, IndirectObject, NameObject,
     NullObject, NumberObject, PdfObject, StreamObject)
from rich.markup import escape

from pdfalyzer.util.adobe_strings import PREV, SIZE, TYPE, XREF, XREF_STREAM
from pdfalyzer.util.helpers.pdf_object_helper import describe_obj
from pdfalyzer.util.logging import log

OK_UNPLACED_TYPES = (BooleanObject, NameObject, NoneType, NullObject, NumberObject)


@dataclass
class PdfTreeVerifier:
    """
    Class to verify that the PDF tree is complete/contains all the nodes in the PDF file.

    Attributes:
        pdfalyzer (Pdfalyzer): The Pdfalyzer instance being verified
    """
    pdfalyzer: 'Pdfalyzer'  # noqa: F821

    def __post_init__(self):
        self._verify_unencountered_are_untraversable()

    def log_missing_node_warnings(self) -> None:
        """Log information about nodes that failed to be placed in the PDF tree."""
        print('')
        unplaced_encountered_nodes = self.pdfalyzer.unplaced_encountered_nodes()

        if len(unplaced_encountered_nodes) > 0:
            msg = f"Some nodes were traversed but never placed: {escape(str(unplaced_encountered_nodes))}\n\n" + \
                   "For link nodes like /First, /Next, /Prev, and /Last this might be no big deal - depends " + \
                   "on the PDF. But for other node typtes this could indicate missing data in the tree.\n"
            log.warning(msg)

        missing_node_ids = self.pdfalyzer.missing_node_ids()
        notable_missing_node_ids = self.notable_missing_node_ids()
        indeterminate_missing_node_ids = [id for id in missing_node_ids if id in self.pdfalyzer._indeterminate_ids]
        all_missing_nodes_msg = lambda s: f"{len(missing_node_ids)} missing node ids{s}: {missing_node_ids}"

        if notable_missing_node_ids:
            log.warning(f"Found {len(notable_missing_node_ids)} important missing node IDs: {notable_missing_node_ids}")

            if missing_node_ids != notable_missing_node_ids:
                log.warning(f"All of the {all_missing_nodes_msg(' including empty objs')}")
        elif missing_node_ids:
            log.warning(f"Identified {all_missing_nodes_msg(' but they are all scalars or empty objects')}")

        for idnum in self.pdfalyzer.missing_node_ids():
            obj = self.pdfalyzer.ref_and_obj_for_id(idnum).obj
            log.warning(f"Missing node ID {idnum} ({type(obj).__name__})")

        if (nodes_without_parents := self.pdfalyzer.nodes_without_parents()):
            node_id_to_child_count = {n.idnum: f"has {len(n.children)} children" for n in nodes_without_parents}
            log.warning(f"These node IDs were parsed but have no parent:\n{node_id_to_child_count}\n")

    def notable_missing_node_ids(self) -> list[int]:
        """Missing idnums that aren't NullObject, NumberObject, etc."""
        notable_ids = []

        for idnum in self.pdfalyzer.missing_node_ids():
            obj = self.pdfalyzer.ref_and_obj_for_id(idnum).obj
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
        return (len(self.pdfalyzer.unplaced_encountered_nodes() + self.notable_missing_node_ids())) == 0

    def _verify_unencountered_are_untraversable(self) -> None:
        """
        Make sure any PDF object IDs we can't find in tree are /ObjStm or /Xref nodes and
        make a final attempt to place a few select kinds of nodes.
        """
        if self.pdfalyzer.max_generation > 0:
            log.warning(f"Verification doesn't check revisions but this PDF's generation is {self.pdfalyzer.max_generation}")  # noqa: E501

        for idnum in self.pdfalyzer.missing_node_ids():
            ref_and_obj = self.pdfalyzer.ref_and_obj_for_id(idnum)
            obj = ref_and_obj.obj

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

            obj_type = obj.get(TYPE)

            if obj_type == XREF:
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
                    self.pdfalyzer.pdf_tree.add_child(self.pdfalyzer._build_or_find_node(ref_and_obj.ref, XREF_STREAM))
            else:
                log.warning(f"{XREF} Obj {idnum} not found in tree!")
