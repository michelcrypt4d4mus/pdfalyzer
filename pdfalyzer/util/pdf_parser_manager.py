import re
from argparse import Namespace
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

from yaralyzer.util.helpers.shell_helper import ShellResult
from yaralyzer.util.logging import log, log_and_print, log_console

from pdfalyzer.config import PdfalyzerConfig
from pdfalyzer.util.helpers.filesystem_helper import (DEFAULT_PDF_PARSER_PATH, PDF_PARSER_PATH_ENV_VAR,
     PDF_PARSER_PY, PROJECT_ROOT, SCRIPTS_DIR, dir_str)
from pdfalyzer.util.exceptions import PdfParserError

# PDF Internal Data Regexes
CONTAINS_STREAM_REGEX = re.compile('\\s+Contains stream$')
PDF_OBJECT_START_REGEX = re.compile('^obj (\\d+) \\d+$')

# Install info
DIDIER_STEVENS_RAW_GITHUB_URL = 'https://raw.githubusercontent.com/DidierStevens/DidierStevensSuite/master/'
INSTALL_SCRIPT_PATH = SCRIPTS_DIR.joinpath('install_didier_stevens_pdf_tools.py').relative_to(PROJECT_ROOT)
PDF_PARSER_TOOL_PATH = DEFAULT_PDF_PARSER_PATH.relative_to(PROJECT_ROOT)
PDF_PARSER_GITHUB_URL = DIDIER_STEVENS_RAW_GITHUB_URL + PDF_PARSER_PY
PDF_PARSER_INSTALL_MSG = f"If you need to install {PDF_PARSER_PY} it's a single .py file that can be " \
                         f"found at {PDF_PARSER_GITHUB_URL}. There's a script in the Pdfalyzer repo that " \
                         f"will install it to {PDF_PARSER_TOOL_PATH} for you at {INSTALL_SCRIPT_PATH}."


@dataclass
class PdfParserManager:
    """Instances of this class manage external calls to Didier Stevens's pdf-parser.py for a given PDF."""
    path_to_pdf: Path
    output_dir: Path
    base_shell_cmd: list[str | Path] = field(init=False)
    object_ids: list[int] = field(default_factory=list)
    object_ids_containing_stream_data: list[int] = field(default_factory=list)

    @classmethod
    def from_args(cls, args: Namespace) -> Self:
        return cls(args.file_to_scan_path, args.output_dir)

    def __post_init__(self):
        if PdfalyzerConfig.pdf_parser_path is None:
            raise PdfParserError(f"{PDF_PARSER_PATH_ENV_VAR} not configured.\n\n{PDF_PARSER_INSTALL_MSG}")

        self.base_shell_cmd = ['python', PdfalyzerConfig.pdf_parser_path, '-O', self.path_to_pdf]
        self.extract_object_ids()

    def extract_object_ids(self) -> None:
        """Examine output of pdf-parser.py to find all object IDs as well as those object IDs that have streams"""
        try:
            result = ShellResult.from_cmd(self.base_shell_cmd, verify_success=True)
            log.debug(result.output_logs(True))
        except Exception as e:
            raise PdfParserError(f"Failed to execute '{self.base_shell_cmd}' ({e})")

        current_object_id = None

        for line in result.stdout.split("\n"):
            if (match := PDF_OBJECT_START_REGEX.match(line)):
                current_object_id = int(match[1])
                self.object_ids.append(current_object_id)

            if current_object_id is None:
                continue

            if CONTAINS_STREAM_REGEX.match(line):
                log.debug(f"{current_object_id} contains a stream!")
                self.object_ids_containing_stream_data.append(current_object_id)

        log.info(f"{self.path_to_pdf} Object IDs: {self.object_ids}")
        log.info(f"{self.path_to_pdf} Objs IDs w/streams: {self.object_ids_containing_stream_data}")

    def extract_all_streams(self) -> None:
        """Use pdf-parser.py to find binary data streams in the PDF and dump each of them to a separate file"""
        output_dir_str = dir_str(self.output_dir)
        log_and_print(f"\nExtracting binary streams in '{self.path_to_pdf}' to files in '{output_dir_str}'...")
        files_written = []

        for object_id in self.object_ids_containing_stream_data:
            stream_dump_file = self.output_dir.joinpath(f'{self.path_to_pdf.name}.object_{object_id}.bin')
            shell_cmd = self.base_shell_cmd + ['-f', '-o', object_id, '-d', stream_dump_file]
            log.info(f'Dumping stream from object {object_id} with cmd:\n\n{shell_cmd}\n')

            try:
                ShellResult.from_cmd(shell_cmd, verify_success=True)
                files_written.append(stream_dump_file)
            except Exception as e:
                log.error(f"Failed to extract object ID {object_id}!")

        log_and_print(f"{len(files_written)} binary streams extracted written to {output_dir_str}.")
        num_failures = len(self.object_ids_containing_stream_data) - len(files_written)

        if num_failures > 0:
            log_console.print(f"{num_failures} streams could not be extracted!", style='bright_red')
