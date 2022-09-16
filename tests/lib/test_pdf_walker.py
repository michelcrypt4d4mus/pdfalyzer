from lib.pdf_walker import PdfWalker


def test_struct_elem_parent(analyzing_malicious_documents_pdf):
    pdf_walker = PdfWalker(analyzing_malicious_documents_pdf)
    struct_elem_node = pdf_walker.find_node_by_idnum(120)
    assert struct_elem_node.parent.idnum == 119
