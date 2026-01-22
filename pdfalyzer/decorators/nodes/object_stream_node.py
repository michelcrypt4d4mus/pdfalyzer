"""
/ObjStm nodes are special nodes containing other nodes in a binary compressed format.

pypdf reads objects from these streams in PdfReader._get_object_from_stream():
    https://github.com/py-pdf/pypdf/blob/4740225eaa67ad2e032e63d0453ea6c80bcae158/pypdf/_reader.py#L343

Didier Stevens parses /ObjStm as a synthetic PDF here: https://github.com/DidierStevens/DidierStevensSuite/blob/master/pdf-parser.py#L1605
Something like:

    offset_stream_data = obj.get_data()[obj.get('/First', 0):]
    log.warning(f"Offset stream: {offset_stream_data[0:100]}")
    stream = BytesIO(offset_stream_data)
    p = PdfReader(stream)
"""
from dataclasses import dataclass, field

from pypdf.generic import DictionaryObject, PdfObject, StreamObject

from pdfalyzer.decorators.pdf_tree_node import PdfTreeNode
from pdfalyzer.util.adobe_strings import *


class ObjStmNode(PdfTreeNode):
    def __post_init__(self):
        super().__post_init__()

        if not isinstance(self.obj, DictionaryObject):
            raise ValueError(f"{OBJ_STM} should be a DictionaryObject")
        elif self.stream_data is None:
            raise ValueError(f"{OBJ_STM} nodes should have stream data!")
        elif FIRST not in self.obj:
            raise ValueError(f"{OBJ_STM} nodes should have a {FIRST} property")

        self.first_byte_idx: int = int(self.obj[FIRST])
        self.objects_bytes = self.stream_data[self.first_byte_idx:]
        self.number_of_objects: int = int(self.obj['/N'])

        # import pdb;pdb.set_trace()
