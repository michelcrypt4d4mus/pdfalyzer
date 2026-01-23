"""
PdfalyzerConfig object holds the unification of configuration options parsed from the command line
as well as those set by environment variables and/or a .pdfalyzer file.
"""
from argparse import Namespace
from os import environ, path
from pathlib import Path
from typing import Callable, TypeVar

from yaralyzer.config import YaralyzerConfig
from yaralyzer.helpers.rich_text_helper import print_fatal_error_and_exit
from yaralyzer.util.logging import log

from pdfalyzer.helpers.filesystem_helper import (DEFAULT_PDF_PARSER_PATH, PDF_PARSER_PATH_ENV_VAR,
     PDF_PARSER_PY, is_executable)
from pdfalyzer.util.constants import PDFALYZE, PDFALYZER_UPPER
from pdfalyzer.util.output_section import ALL_STREAMS

T = TypeVar('T')


class PdfalyzerConfig:
    pdf_parser_path: Path | None = None
    _args: Namespace = Namespace()

    @classmethod
    def get_env_value(cls, env_var: str, var_type: Callable[[str], T] = str) -> T | None:
        """If called with 'output_dir' it will check env value of 'PDFALYZER_OUTPUT_DIR'."""
        env_var = f"{PDFALYZER_UPPER}_{env_var}".upper() if not env_var.startswith(PDFALYZER_UPPER) else env_var
        env_value = environ.get(env_var)
        log.debug(f"Checked env for '{env_var}', found '{env_value}'")
        env_value = var_type(env_value) if env_value else None

        if isinstance(env_value, Path):
            if not env_value.exists():
                print_fatal_error_and_exit(f"{env_var} is '{env_value}' but that path doesn't exist!")

        return env_value

    @classmethod
    def get_export_basepath(cls, export_method: Callable) -> str:
        """Build the path to an output file - everything but the extension"""
        export_type = export_method.__name__.removeprefix('print_')
        export_basename = f"{cls._args.export_basename}.{export_type}"

        if export_type == 'streams_analysis':
            if cls._args.streams != ALL_STREAMS:
                export_basename += f"_streamid{cls._args.streams}"

            export_basename += f"_maxdecode{YaralyzerConfig.args.max_decode_length}"

            if cls._args.extract_quoteds:
                export_basename += f"_extractquoteds-{','.join(cls._args.extract_quoteds)}"

        export_basename += cls._args.file_suffix

        if not cls._args.no_timestamps:
            export_basename += f"___{PDFALYZE}d_{cls._args.invoked_at_str}"

        return path.join(cls._args.output_dir, export_basename)

    @classmethod
    def find_pdf_parser(cls) -> None:
        """Find the location of Didier Stevens's pdf-parser.py on the current system."""
        cls.pdf_parser_path = cls.get_env_value(PDF_PARSER_PATH_ENV_VAR, Path) or DEFAULT_PDF_PARSER_PATH

        if cls.pdf_parser_path.exists():
            if not is_executable(cls.pdf_parser_path):
                log.warning(f"{PDF_PARSER_PY} found at {cls.pdf_parser_path} but it's not executable...")
        else:
            log.warning(f"Configured PDF_PARSER_PATH is '{cls.pdf_parser_path}' but that file doesn't exist!")
            cls.pdf_parser_path = None


PdfalyzerConfig.find_pdf_parser()
