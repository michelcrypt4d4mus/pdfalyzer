"""
Verify that the PDF tree is complete/contains all the nodes in the PDF file.
"""
from pypdf.errors import PdfReadError
from pypdf.generic import IndirectObject, NameObject, NumberObject
from rich.markup import escape
from yaralyzer.output.rich_console import console
from yaralyzer.util.logging import log

from pdfalyzer.util.adobe_strings import *


class PdfTreeVerifier:
    def __init__(self, pdfalyzer: 'Pdfalyzer') -> None:
        self.pdfalyzer = pdfalyzer

    def verify_all_nodes_encountered_are_in_tree(self) -> None:
        """Make sure every node we can see is reachable from the root of the tree"""
        missing_nodes = [
            node for idnum, node in self.pdfalyzer.nodes_encountered.items()
            if self.pdfalyzer.find_node_by_idnum(idnum) is None
        ]

        if len(missing_nodes) > 0:
            msg = f"Nodes were traversed but never placed: {escape(str(missing_nodes))}\n" + \
                   "For link nodes like /First, /Next, /Prev, and /Last this might be no big deal - depends " + \
                   "on the PDF. But for other node typtes this could indicate missing data in the tree."
            console.print(msg)
            log.warning(msg)

    def verify_unencountered_are_untraversable(self) -> None:
        """Make sure any PDF object IDs we can't find in tree are /ObjStm or /Xref nodes."""
        if self.pdfalyzer.pdf_size is None:
            log.warning(f"{SIZE} not found in PDF trailer; cannot verify all nodes are in tree")
            return
        if self.pdfalyzer.max_generation > 0:
            log.warning(f"Methodd doesn't check revisions but this doc is generation {self.pdfalyzer.max_generation}")

        # We expect to see all ordinals up to the number of nodes /Trailer claims exist as obj. IDs.
        missing_node_ids = [i for i in range(1, self.pdfalyzer.pdf_size) if self.pdfalyzer.find_node_by_idnum(i) is None]

        for idnum in missing_node_ids:
            ref = IndirectObject(idnum, self.pdfalyzer.max_generation, self.pdfalyzer.pdf_reader)

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
