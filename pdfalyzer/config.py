"""
PdfalyzerConfig object holds the unification of configuration options parsed from the command line
as well as those set by environment variables and/or a .pdfalyzer file.
"""
from os import path
from pathlib import Path
from typing import Callable, TypeVar

from yaralyzer.config import YaralyzerConfig
from yaralyzer.util.argument_parser import rules, tuning
from yaralyzer.util.constants import MAX_FILENAME_LENGTH
from yaralyzer.util.logging import log

from pdfalyzer.detection.yaralyzer_helper import YARA_RULES_FILES
from pdfalyzer.output.theme import COMPLETE_THEME_DICT
from pdfalyzer.util.constants import PDFALYZE, PDFALYZER_UPPER
from pdfalyzer.util.helpers.filesystem_helper import DEFAULT_PDF_PARSER_PATH, PDF_PARSER_PATH_ENV_VAR
from pdfalyzer.util.output_section import ALL_STREAMS

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
        if cls._custom_yara_rules_file_basenames():
            export_basename += f"__scannedby_" + ','.join(cls._custom_yara_rules_file_basenames())

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
    def _custom_yara_rules_file_basenames(cls) -> list[str]:
        """Returns yara rules files requested by -Y option only (excludes included `YARA_RULES_FILES`)."""
        # TODO: YaralyzerConfig is updating the same ._args this class uses when _build-yaralyzer() is called (i think)
        # so this class's ._args.yara_rules_files ends up with all the defaults PDF yara rules.
        yara_rules_files = cls.args.yara_rules_files or []
        yara_rules_basenames =  [Path(f).name for f in yara_rules_files if not Path(f).name in YARA_RULES_FILES]
        return sorted(yara_rules_basenames)

    @classmethod
    def _set_class_vars_from_env(cls) -> None:
        """Set log related class vars and find path to pdf-parser.py (if any)."""
        super()._set_class_vars_from_env()
        cls.pdf_parser_path = cls.get_env_value(PDF_PARSER_PATH_ENV_VAR, Path) or DEFAULT_PDF_PARSER_PATH

        if not cls.pdf_parser_path.exists():
            log.warning(f"Configured PDF_PARSER_PATH is '{cls.pdf_parser_path}' but that file doesn't exist!")
            cls.pdf_parser_path = None
