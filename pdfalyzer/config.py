"""
PdfalyzerConfig object holds the unification of configuration options parsed from the command line
as well as those set by environment variables and/or a .pdfalyzer file.
"""
import importlib.resources
from argparse import Namespace
from os import environ, path
from pathlib import Path
from typing import Callable, Type, TypeVar

from yaralyzer.config import YaralyzerConfig
from yaralyzer.helpers.env_helper import is_env_var_set_and_not_false, is_invoked_by_pytest
from yaralyzer.helpers.rich_text_helper import print_fatal_error_and_exit
from yaralyzer.util.logging import log

from pdfalyzer.util.output_section import ALL_STREAMS

PDFALYZE = 'pdfalyze'
PDFALYZER = f"{PDFALYZE}r"
PDFALYZER_UPPER = PDFALYZER.upper()
PROJECT_ROOT = Path(str(importlib.resources.files(PDFALYZER))).parent
SCRIPTS_DIR = PROJECT_ROOT.joinpath('scripts')
TOOLS_DIR = PROJECT_ROOT.joinpath('tools')
T = TypeVar('T')

# 3rd party pdf-parser.py
PDF_PARSER_PY = 'pdf-parser.py'
PDF_PARSER_EXECUTABLE_ENV_VAR = 'PDFALYZER_PDF_PARSER_PY_PATH'
DEFAULT_PDF_PARSER_EXECUTABLE = TOOLS_DIR.joinpath(PDF_PARSER_PY)


class PdfalyzerConfig:
    _args: Namespace = Namespace()

    # Path to Didier Stevens's pdf-parser.py
    if is_env_var_set_and_not_false(PDF_PARSER_EXECUTABLE_ENV_VAR):
        PDF_PARSER_EXECUTABLE = Path(environ[PDF_PARSER_EXECUTABLE_ENV_VAR])

        if PDF_PARSER_EXECUTABLE.is_dir():
            PDF_PARSER_EXECUTABLE = PDF_PARSER_EXECUTABLE.joinpath(PDF_PARSER_PY)

        if not PDF_PARSER_EXECUTABLE.exists():
            log.warning(f"{PDF_PARSER_PY} not found at {PDF_PARSER_EXECUTABLE_ENV_VAR}={PDF_PARSER_EXECUTABLE}")
            PDF_PARSER_EXECUTABLE = None
    elif is_invoked_by_pytest():
        PDF_PARSER_EXECUTABLE = DEFAULT_PDF_PARSER_EXECUTABLE
    else:
        if path.exists(DEFAULT_PDF_PARSER_EXECUTABLE):
            PDF_PARSER_EXECUTABLE = DEFAULT_PDF_PARSER_EXECUTABLE
        else:
            PDF_PARSER_EXECUTABLE = None

    @classmethod
    def get_env_value(cls, env_var_name: str, var_type: Callable[[str], T] = str) -> T | None:
        """If called with 'output_dir' it will check env value of 'PDFALYZER_OUTPUT_DIR'."""
        env_var = f"{PDFALYZER_UPPER}_{env_var_name}".upper()
        env_value = environ.get(env_var)
        log.debug(f"Checked env for '{env_var}', found '{env_value}'")
        env_value = var_type(env_value) if env_value else None

        if isinstance(env_value, Path):
            if not env_value.exists():
                print_fatal_error_and_exit(f"{env_var}='{env_value}' but that path doesn't exist")

        return env_value

    @classmethod
    def get_output_basepath(cls, export_method: Callable) -> str:
        """Build the path to an output file - everything but the extension"""
        export_type = export_method.__name__.removeprefix('print_')
        output_basename = f"{cls._args.output_basename}.{export_type}"

        if export_type == 'streams_analysis':
            if cls._args.streams != ALL_STREAMS:
                output_basename += f"_streamid{cls._args.streams}"

            output_basename += f"_maxdecode{YaralyzerConfig.args.max_decode_length}"

            if cls._args.extract_quoteds:
                output_basename += f"_extractquoteds-{','.join(cls._args.extract_quoteds)}"

        output_basename += cls._args.file_suffix
        output_basename += '' if is_invoked_by_pytest() else f"___pdfalyzed_{cls._args.invoked_at_str}"
        return path.join(cls._args.output_dir, output_basename)
