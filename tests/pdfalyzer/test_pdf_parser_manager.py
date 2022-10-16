from pdfalyzer.util.pdf_parser_manager import PdfParserManager


def test_pdf_parser_manager(analyzing_malicious_pdf_path):
    pdf_parser_manager = PdfParserManager(analyzing_malicious_pdf_path)
    assert pdf_parser_manager.object_ids_containing_stream_data ==  [4, 71, 411, 412, 416, 419, 421, 423, 424, 426]
