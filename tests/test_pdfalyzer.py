"""
Test Pdfalyzer() methods.
"""


def test_is_in_tree(analyzing_malicious_pdfalyzer, page_node):
    assert analyzing_malicious_pdfalyzer.is_in_tree(page_node)


def test_font_extraction(attachment_pdf_pdfalyzer):
    assert len(attachment_pdf_pdfalyzer.font_infos) == 3
