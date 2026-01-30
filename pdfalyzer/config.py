"""
PdfalyzerConfig object holds the unification of configuration options parsed from the command line
as well as those set by environment variables and/or a .pdfalyzer file.
"""
import logging
from argparse import Namespace
from os import path
from pathlib import Path
from typing import Callable, TypeVar

from yaralyzer.config import YaralyzerConfig
from yaralyzer.util.argument_parser import rules, tuning
from yaralyzer.util.classproperty import classproperty
from yaralyzer.util.constants import MAX_FILENAME_LENGTH
from yaralyzer.util.exceptions import print_fatal_error_and_exit
from yaralyzer.util.helpers.env_helper import is_env_var_set_and_not_false, stderr_notification

from pdfalyzer.output.theme import COMPLETE_THEME_DICT
from pdfalyzer.util.constants import PDF_PARSER_NOT_FOUND_MSG, PDFALYZE, PDFALYZER_UPPER
from pdfalyzer.util.helpers.filesystem_helper import DEFAULT_PDF_PARSER_PATH
from pdfalyzer.util.logging import log, log_handler_kwargs
from pdfalyzer.util.output_section import ALL_STREAMS

PDF_PARSER_PATH_ENV_VAR = 'PDF_PARSER_PY_PATH'  # Github workflow depends on this value!
T = TypeVar('T')

# These options will be read from env vars prefixed with YARALYZER, not PDFALYZER
# TODO: for some reasonm PDFALYZER_PATTERNS_LABEL and PDFALYZER_REGEX_MODIFIER are showing up
YARALYZER_SPECIFIC_OPTIONS = [
    action.dest
    for argument_group in [rules, tuning]
    for action in argument_group._group_actions
]


class PdfalyzerConfig(YaralyzerConfig):
    """Handles parsing of command line args and environment variables for Pdfalyzer."""

    # Override the class vars of same name in YaralyzerConfig
    ENV_VAR_PREFIX = PDFALYZER_UPPER
    COLOR_THEME = COMPLETE_THEME_DICT
    ONLY_CLI_ARGS = YaralyzerConfig.ONLY_CLI_ARGS + ['extract_binary_streams']

    pdf_parser_path: Path | None = None
    _log_handler_kwargs = dict(log_handler_kwargs)

    @classproperty
    def loggers(cls) -> list[logging.Logger]:
        """Returns both the `Logger` for Pdfalyzer as well as Yaralyzer."""
        return [cls.log, YaralyzerConfig.log]

    @classmethod
    def get_export_basepath(cls, export_method: Callable) -> str:
        """Build the path to an output file - everything but the extension"""
        export_type = export_method.__name__.removeprefix('print_')
        export_basename = f"{cls.args._export_basename}.{export_type}"

        if export_type == 'streams_analysis':
            if cls.args.streams != ALL_STREAMS:
                export_basename += f"_streamid{cls.args.streams}"

            export_basename += f"_maxdecode{YaralyzerConfig.args.max_decode_length}"

            if cls.args.extract_quoteds:
                export_basename += f"_extractquoteds-{','.join(cls.args.extract_quoteds)}"
            if cls.args.suppress_boms:
                export_basename += '_noBOMs'

        # YARA rules suffixes
        if cls.args.yara_rules_files:
            export_basename += f"__scannedby_" + ','.join(sorted([f.name for f in cls.args.yara_rules_files]))

            if cls.args.no_default_yara_rules:
                export_basename += '_customrulesonly'

        export_basename += cls.args.file_suffix

        if not cls.args.no_timestamps:
            export_basename += f"___{PDFALYZE}d_{cls.args._invoked_at_str}"

        max_filename_length = MAX_FILENAME_LENGTH - len(str(cls.args.output_dir.resolve()))
        return path.join(cls.args.output_dir, export_basename[:max_filename_length])

    @classmethod
    def prefixed_env_var(cls, var: str) -> str:
        """Turns 'LOG_DIR' into 'PDFALYZER_LOG_DIR' etc. Overloads superclass method."""
        prefix = super().ENV_VAR_PREFIX if var in YARALYZER_SPECIFIC_OPTIONS else cls.ENV_VAR_PREFIX
        return (var if var.startswith(prefix) else f"{prefix}_{var}").upper()

    @classmethod
    def _parse_arguments(cls, args: Namespace) -> Namespace:
        """Overloads/extends YaralyzerConfig method of the same name."""
        args = super()._parse_arguments(args)
        args.extract_quoteds = args.extract_quoteds or []
        args._yaralyzer_standalone_mode = False  # TODO: this sucks
        args._export_basename = f"{args.file_prefix}{args.file_to_scan_path.name}"

        if not args.streams:
            if args.extract_quoteds:
                log.warning("--extract-quoted does nothing if --streams is not selected")
            if args.suppress_boms:
                log.warning("--suppress-boms has nothing to suppress if --streams is not selected")

        if args.no_default_yara_rules and not any(getattr(args, opt.dest) for opt in rules._group_actions):
            print_fatal_error_and_exit("--no-default-yara-rules requires at least one YARA rule argument")

        return args

    @classmethod
    def _set_class_vars_from_env(cls) -> None:
        """Set log related class vars and find path to pdf-parser.py (if any)."""
        super()._set_class_vars_from_env()
        cls.pdf_parser_path = cls.get_env_value(PDF_PARSER_PATH_ENV_VAR, Path) or DEFAULT_PDF_PARSER_PATH

        if not cls.pdf_parser_path.exists():
            if is_env_var_set_and_not_false(PDF_PARSER_PATH_ENV_VAR):
                log.warning(f"Configured {PDF_PARSER_PATH_ENV_VAR}='{cls.pdf_parser_path}' but no such file exists!")
            else:
                stderr_notification(PDF_PARSER_NOT_FOUND_MSG)

            cls.pdf_parser_path = None
