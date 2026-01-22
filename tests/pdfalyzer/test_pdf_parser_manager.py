from pathlib import Path

from pdfalyzer.helpers.filesystem_helper import file_sizes_in_dir
from pdfalyzer.util.pdf_parser_manager import PdfParserManager

OBJ_SIZES = {
    4: 104658,
    71: 25191,
    411: 873,
    412: 150868,
    416: 108836,
    419: 53796,
    421: 47832,
    423: 95696,
    424: 10,
    426: 2982,
}


def test_pdf_parser_manager(pdf_parser_manager_args, tmp_dir):
    pdf_parser_manager = PdfParserManager(pdf_parser_manager_args)
    assert pdf_parser_manager.object_ids_containing_stream_data == sorted(id for id in OBJ_SIZES)
    pdf_parser_manager.extract_all_streams()
    file_basename = Path(pdf_parser_manager_args.file_to_scan_path).name

    assert file_sizes_in_dir(tmp_dir, 'bin') == {
        tmp_dir.joinpath(f"{file_basename}.object_{id}.bin"): size
        for id, size in OBJ_SIZES.items()
    }
