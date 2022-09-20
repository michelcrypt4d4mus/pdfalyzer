import pytest

from lib.pdf_parser_manager import PdfParserManager
from lib.pdf_walker import PdfWalker
from lib.util.logging import log


class TestPdfWalker:
    @pytest.fixture(scope="class")
    def pdf_walker(self, analyzing_malicious_documents_pdf):
        return PdfWalker(analyzing_malicious_documents_pdf)

    def test_struct_elem_parent(self, pdf_walker):
        struct_elem_node = pdf_walker.find_node_by_idnum(120)
        assert struct_elem_node.parent.idnum == 119

    def test_all_nodes_in_tree(self, pdf_walker, analyzing_malicious_documents_pdf):
        for object_id in PdfParserManager(analyzing_malicious_documents_pdf).object_ids:
            if object_id == 71:
                # 71 is the ID of the object stream holding many of the /StructElem
                continue
            elif object_id == 67:
                # 67 is an object without any references or data
                continue
            elif object_id == 426:
                # 426 is a Cross-reference stream containing the same info as the trailer
                continue

            assert pdf_walker.find_node_by_idnum(object_id) is not None, f"Expected {object_id} to appear in tree."
