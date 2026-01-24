"""
PdfalyzerConfig object holds the unification of configuration options parsed from the command line
as well as those set by environment variables and/or a .pdfalyzer file.
"""
from os import path
from pathlib import Path
from typing import Callable, TypeVar

from yaralyzer.config import YaralyzerConfig
from yaralyzer.util.argument_parser import source, tuning
from yaralyzer.util.logging import log

from pdfalyzer.helpers.filesystem_helper import (DEFAULT_PDF_PARSER_PATH, PDF_PARSER_PATH_ENV_VAR,
     PDF_PARSER_PY, is_executable)
from pdfalyzer.util.constants import PDFALYZE, PDFALYZER_UPPER
from pdfalyzer.util.output_section import ALL_STREAMS

T = TypeVar('T')

# These options will be read from env vars prefixed with YARALYZER, not PDFALYZER
YARALYZER_SPECIFIC_OPTIONS = [
    action.dest
    for argument_group in [source, tuning]
    for action in argument_group._group_actions
]


class PdfalyzerConfig(YaralyzerConfig):
    # Overrides the class var of same name in YaralyzerConfig
    ENV_VAR_PREFIX = PDFALYZER_UPPER

    pdf_parser_path: Path | None = None

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

    @classmethod
    def get_export_basepath(cls, export_method: Callable) -> str:
        """Build the path to an output file - everything but the extension"""
        export_type = export_method.__name__.removeprefix('print_')
        export_basename = f"{cls.args.export_basename}.{export_type}"

        if export_type == 'streams_analysis':
            if cls.args.streams != ALL_STREAMS:
                export_basename += f"_streamid{cls.args.streams}"

            export_basename += f"_maxdecode{YaralyzerConfig.args.max_decode_length}"

            if cls.args.extract_quoteds:
                export_basename += f"_extractquoteds-{','.join(cls.args.extract_quoteds)}"

        export_basename += cls.args.file_suffix

        if not cls.args.no_timestamps:
            export_basename += f"___{PDFALYZE}d_{cls.args.invoked_at_str}"

        return path.join(cls.args.output_dir, export_basename)

    @classmethod
    def prefixed_env_var(cls, var: str) -> str:
        """Turns 'LOG_DIR' into 'PDFALYZER_LOG_DIR' etc. Overloads superclass method."""
        prefix = super().ENV_VAR_PREFIX if var in YARALYZER_SPECIFIC_OPTIONS else cls.ENV_VAR_PREFIX
        return (var if var.startswith(prefix) else f"{prefix}_{var}").upper()


PdfalyzerConfig.set_log_vars()
PdfalyzerConfig.find_pdf_parser()
