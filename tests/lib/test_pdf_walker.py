import pytest

from lib.pdf_parser_manager import PdfParserManager
from lib.util.logging import log


class TestPdfWalker:
    def test_struct_elem_parent(self, analyzing_malicious_documents_pdf_walker):
        struct_elem_node = analyzing_malicious_documents_pdf_walker.find_node_by_idnum(120)
        assert struct_elem_node.parent.idnum == 119

    def test_all_nodes_in_tree(self, analyzing_malicious_documents_pdf_walker, analyzing_malicious_documents_pdf_path):
        for object_id in PdfParserManager(analyzing_malicious_documents_pdf_path).object_ids:
            if object_id == 71:
                # 71 is the ID of the object stream holding many of the /StructElem
                continue
            elif object_id == 67:
                # 67 is an object without any references or data
                continue
            elif object_id == 426:
                # 426 is a Cross-reference stream containing the same info as the trailer
                continue

            node = analyzing_malicious_documents_pdf_walker.find_node_by_idnum(object_id)
            assert node is not None, f"Expected {object_id} to appear in tree."
