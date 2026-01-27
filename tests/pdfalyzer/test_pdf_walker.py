"""Use pdf-parser.py to validate our attempt to walk all the nodes in a PDF."""
from pdfalyzer.util.pdf_parser_manager import PdfParserManager


class TestPdfalyzer:
    def test_struct_elem_parent(self, analyzing_malicious_pdfalyzer):
        struct_elem_node = analyzing_malicious_pdfalyzer.find_node_by_idnum(120)
        assert struct_elem_node.parent.idnum == 119

    def test_all_nodes_in_tree(self, analyzing_malicious_pdfalyzer, pdf_parser_manager_args):
        for object_id in PdfParserManager.from_args(pdf_parser_manager_args).object_ids:
            if object_id == 71:
                continue  # 71 is the ID of the object stream holding many of the /StructElem
            elif object_id == 67:
                continue  # 67 is an object without any references or data
            elif object_id == 426:
                continue  # 426 is a Cross-reference stream containing the same info as the trailer

            node = analyzing_malicious_pdfalyzer.find_node_by_idnum(object_id)
            assert node is not None, f"Expected {object_id} to appear in tree."
