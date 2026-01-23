import re
from argparse import Namespace
from dataclasses import dataclass, field
from os import environ
from pathlib import Path
from subprocess import check_output

from yaralyzer.util.logging import log, log_and_print

from pdfalyzer.config import PdfalyzerConfig
from pdfalyzer.helpers.filesystem_helper import (DEFAULT_PDF_PARSER_EXECUTABLE, PDF_PARSER_EXECUTABLE_ENV_VAR,
     PDF_PARSER_PY, PROJECT_ROOT, SCRIPTS_DIR, is_executable, relative_path)
from pdfalyzer.util.exceptions import PdfParserError

# PDF Internal Data Regexes
PDF_OBJECT_START_REGEX = re.compile('^obj (\\d+) \\d+$')
CONTAINS_STREAM_REGEX = re.compile('\\s+Contains stream$')

# Install info
DIDIER_STEVENS_RAW_GITHUB_URL = 'https://raw.githubusercontent.com/DidierStevens/DidierStevensSuite/master/'
INSTALL_SCRIPT_PATH = SCRIPTS_DIR.joinpath('install_didier_stevens_pdf_tools.sh').relative_to(PROJECT_ROOT)
PDF_PARSER_TOOL_PATH = DEFAULT_PDF_PARSER_EXECUTABLE.relative_to(PROJECT_ROOT)
PDF_PARSER_GITHUB_URL = DIDIER_STEVENS_RAW_GITHUB_URL + 'pdf-parser.py'
PDF_PARSER_INSTALL_MSG = f"If you need to install pdf-parser.py it's a single .py file that can be " \
                         f"found at {PDF_PARSER_GITHUB_URL}. There's a script in the Pdfalyzer repo that " \
                         f"will install it to {PDF_PARSER_TOOL_PATH} for you at {INSTALL_SCRIPT_PATH}."


@dataclass
class PdfParserManager:
    """Instances of this class manage external calls to Didier Stevens's pdf-parser.py for a given PDF."""
    args: Namespace
    base_shell_cmd: str = field(init=False)
    object_ids: list[int] = field(default_factory=list)
    object_ids_containing_stream_data: list[int] = field(default_factory=list)
    path_to_pdf: Path = field(init=False)

    def __post_init__(self):
        if PdfalyzerConfig.PDF_PARSER_EXECUTABLE is None:
            raise PdfParserError(f"{PDF_PARSER_EXECUTABLE_ENV_VAR} not configured.\n\n{PDF_PARSER_INSTALL_MSG}")

        pdf_parser_relative_path = relative_path(PdfalyzerConfig.PDF_PARSER_EXECUTABLE)

        if not PdfalyzerConfig.PDF_PARSER_EXECUTABLE.exists():
            msg = f"{PDF_PARSER_PY} not found at configured location '{pdf_parser_relative_path}'\n\n"
            raise PdfParserError(msg + PDF_PARSER_INSTALL_MSG)
        elif not is_executable(PdfalyzerConfig.PDF_PARSER_EXECUTABLE):
            raise PdfParserError(f"{pdf_parser_relative_path} is not executable!")

        self.path_to_pdf = Path(self.args.file_to_scan_path)
        self.base_shell_cmd = f'{PdfalyzerConfig.PDF_PARSER_EXECUTABLE} -O "{self.path_to_pdf}"'
        self.object_ids_containing_stream_data = []
        self.extract_object_ids()

    def extract_object_ids(self) -> None:
        """Examine output of pdf-parser.py to find all object IDs as well as those object IDs that have streams"""
        try:
            pdf_parser_output = check_output(self.base_shell_cmd, env=environ, shell=True, text=True)
        except Exception as e:
            raise PdfParserError(f"Failed to execute '{self.base_shell_cmd}' ({e})")

        current_object_id = None

        for line in pdf_parser_output.split("\n"):
            match = PDF_OBJECT_START_REGEX.match(line)

            if match:
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
        log_and_print(f"Extracting binary streams in '{self.path_to_pdf}' to files in '{self.args.output_dir}'...")

        for object_id in self.object_ids_containing_stream_data:
            stream_dump_file = self.args.output_dir.joinpath(f'{self.path_to_pdf.name}.object_{object_id}.bin')
            shell_cmd = self.base_shell_cmd + f' -f -o {object_id} -d "{stream_dump_file}"'
            log.info(f'Dumping stream from object {object_id} with cmd:\n\n{shell_cmd}\n')

            try:
                check_output(shell_cmd, env=environ, shell=True, text=True)
            except Exception as e:
                log.error(f"Failed to extract object ID {object_id}!")

        output_dir_str = str(self.args.output_dir) + ('/' if str(self.args.output_dir).endswith('/') else '')
        log_and_print(f"Binary stream extraction complete, {len(self.object_ids_containing_stream_data)} "
                      f"files written to '{output_dir_str}'.\n")
