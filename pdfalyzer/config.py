import importlib.resources
from argparse import Namespace
from os import environ, pardir, path

from yaralyzer.config import YaralyzerConfig, is_env_var_set_and_not_false, is_invoked_by_pytest

PDFALYZE = 'pdfalyze'
ALL_STREAMS = -1
PYTEST_FLAG = 'INVOKED_BY_PYTEST'
PROJECT_ROOT = path.join(str(importlib.resources.files('pdfalyzer')), pardir)

# 3rd part pdf-parser.py
PDF_PARSER_EXECUTABLE_ENV_VAR = 'PDFALYZER_PDF_PARSER_PY_PATH'
DEFAULT_PDF_PARSER_EXECUTABLE = path.join(PROJECT_ROOT, 'tools', 'pdf-parser.py')


class PdfalyzerConfig:
    _args: Namespace = Namespace()

    # Path to Didier Stevens's pdf-parser.py
    if is_env_var_set_and_not_false(PDF_PARSER_EXECUTABLE_ENV_VAR):
        PDF_PARSER_EXECUTABLE = path.join(environ[PDF_PARSER_EXECUTABLE_ENV_VAR], 'pdf-parser.py')
    elif is_invoked_by_pytest():
        PDF_PARSER_EXECUTABLE = DEFAULT_PDF_PARSER_EXECUTABLE
    else:
        if path.exists(DEFAULT_PDF_PARSER_EXECUTABLE):
            PDF_PARSER_EXECUTABLE = DEFAULT_PDF_PARSER_EXECUTABLE
        else:
            PDF_PARSER_EXECUTABLE = None

    @classmethod
    def get_output_basepath(cls, export_method: str) -> str:
        """Build the path to an output file - everything but the extension"""
        export_type = export_method.__name__.removeprefix('print_')
        output_basename = f"{cls._args.output_basename}.{export_type}"

        if export_type == 'streams_analysis':
            if cls._args.streams != ALL_STREAMS:
                output_basename += f"_streamid{cls._args.streams}"

            output_basename += f"_maxdecode{YaralyzerConfig.args.max_decode_length}"

            if cls._args.extract_quoteds:
                output_basename += f"_extractquoteds-{','.join(cls._args.extract_quoteds)}"

        return path.join(
            cls._args.output_dir,
            output_basename + cls._args.file_suffix + f"___pdfalyzed_{cls._args.invoked_at_str}"
        )
