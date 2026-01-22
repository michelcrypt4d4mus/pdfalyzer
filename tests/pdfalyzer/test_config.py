from pdfalyzer.config import PdfalyzerConfig
from pdfalyzer.output.pdfalyzer_presenter import PdfalyzerPresenter
from pdfalyzer.util.argument_parser import parse_arguments


def test_get_output_basepath(export_analyzing_malicious_args, analyzing_malicious_pdfalyzer, tmp_dir):
    parse_arguments(export_analyzing_malicious_args)
    presenter = PdfalyzerPresenter(analyzing_malicious_pdfalyzer)
    output_path = PdfalyzerConfig.get_output_basepath(presenter.print_document_info)
    assert output_path == (f'{tmp_dir}/analyzing-malicious-document-files.pdf.document_info')
