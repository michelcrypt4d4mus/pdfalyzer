from contextlib import contextmanager
from os import environ
from pathlib import Path

from pdfalyzer.config import PdfalyzerConfig
from pdfalyzer.output.pdfalyzer_presenter import PdfalyzerPresenter
from pdfalyzer.util.argument_parser import parse_arguments
from pdfalyzer.util.constants import PDFALYZER_UPPER


@contextmanager
def setup_and_tear_down_env_vars(env_vars: dict[str, str]):
    old_environ = dict(environ)
    environ.update(env_vars)
    yield
    environ.clear()
    environ.update(old_environ)


def test_get_export_basepath(export_analyzing_malicious_args, analyzing_malicious_pdfalyzer, tmp_dir):
    parse_arguments(export_analyzing_malicious_args + ['--no-timestamps'])
    presenter = PdfalyzerPresenter(analyzing_malicious_pdfalyzer)
    output_path = PdfalyzerConfig.get_export_basepath(presenter.print_document_info)
    assert output_path == (f'{tmp_dir}/analyzing-malicious-document-files.pdf.document_info')


def test_get_env_value(tmp_dir):
    tmp_dir_str = str(tmp_dir)

    with setup_and_tear_down_env_vars({f"{PDFALYZER_UPPER}_OUTPUT_DIR": tmp_dir_str}):
        assert PdfalyzerConfig.get_env_value('OUTPUT_DIR') == tmp_dir_str
        assert PdfalyzerConfig.get_env_value('output_dir') == tmp_dir_str
        assert PdfalyzerConfig.get_env_value('OUTPUT_DIR', Path) == tmp_dir
