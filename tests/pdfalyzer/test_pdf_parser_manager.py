from argparse import Namespace

from pdfalyzer.util.pdf_parser_manager import PdfParserManager


def test_pdf_parser_manager(pdf_parser_manager_args):
    pdf_parser_manager = PdfParserManager(pdf_parser_manager_args)
    assert pdf_parser_manager.object_ids_containing_stream_data == [4, 71, 411, 412, 416, 419, 421, 423, 424, 426]
