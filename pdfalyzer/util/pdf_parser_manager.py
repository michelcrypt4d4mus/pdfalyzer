import os
import re
import stat
import sys
from argparse import Namespace
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

from rich.prompt import Prompt
from rich.text import Text
from yaralyzer.util.exceptions import print_fatal_error_and_exit
from yaralyzer.util.helpers.shell_helper import ShellResult
from yaralyzer.util.logging import log, log_and_print, log_console

from pdfalyzer.config import PdfalyzerConfig
from pdfalyzer.util.exceptions import PdfParserError
from pdfalyzer.util.helpers.filesystem_helper import PDF_PARSER_PATH_ENV_VAR, PDF_PARSER_PY, dir_str
from pdfalyzer.util.helpers.interaction_helper import ask_to_proceed

# PDF Internal Data Regexes
CONTAINS_STREAM_REGEX = re.compile(r'\s+Contains stream$')
PDF_OBJECT_START_REGEX = re.compile(r'^obj (\d+) \d+$')

# Installation of pdf-parser.py info
PDF_TOOLS_FILES = [PDF_PARSER_PY, 'pdfid.py', 'xorsearch.py']
DIDIER_STEVENS_RAW_GITHUB_URL = 'https://raw.githubusercontent.com/DidierStevens/DidierStevensSuite/master/'
PDF_PARSER_GITHUB_URL = DIDIER_STEVENS_RAW_GITHUB_URL + PDF_PARSER_PY

DEFAULT_PDF_TOOLS_DIR = Path('pdf_tools')
INSTALL_SCRIPT_NAME = 'install_didier_stevens_pdf_tools'
INSTALL_STYLE = 'wheat4'
INSTALL_STYLE_BOLD = f"{INSTALL_STYLE} bold"

INSTALL_DEFAULT_TXT = Text("(default: ", style='dim').append(f"./{DEFAULT_PDF_TOOLS_DIR}", style='cyan').append(')')
INSTALL_PROMPT = Text("\nWhere would you like to install Didier Stevens's PDF tools? ", style=INSTALL_STYLE_BOLD) + INSTALL_DEFAULT_TXT

TOOLS_INSTALL_MSG = f"If you need to install {PDF_PARSER_PY} it's a single .py file that can be " \
                    f"found at {PDF_PARSER_GITHUB_URL}. There's also a script that comes with Pdfalyzer " \
                    f"that will install it for you if you run:\n\n    {INSTALL_SCRIPT_NAME}\n\n"


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
        """Alternate constructor that takes the result of an `ArgumentParser.`"""
        return cls(args.file_to_scan_path, args.output_dir)

    def __post_init__(self):
        if PdfalyzerConfig.pdf_parser_path is None:
            raise PdfParserError(f"{PDF_PARSER_PATH_ENV_VAR} not configured.\n\n{TOOLS_INSTALL_MSG}")

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

        log_and_print(f"{len(files_written)} extracted binary streams were written to {output_dir_str}.")
        num_failures = len(self.object_ids_containing_stream_data) - len(files_written)

        if num_failures > 0:
            log_console.print(f"{num_failures} streams could not be extracted!", style='bright_red')

    @staticmethod
    def install_didier_stevens_tools() -> None:
        """Get Didier Stevens's pdf-parser.py and pdfid.py from github."""
        try:
            import requests
        except ModuleNotFoundError:
            print_fatal_error_and_exit(f"Python 'requests' package not installed. Maybe try:\n\npip install pdaflyzer[extract]\n\n")

        def log_status(msg, **kwargs) -> None:
            log_console.print(f"  -> {msg}", style=INSTALL_STYLE, **kwargs)

        install_dir = Prompt.ask(INSTALL_PROMPT, default=str(DEFAULT_PDF_TOOLS_DIR), show_default=False)
        install_dir = Path(install_dir)

        if not install_dir.exists():
            ask_to_proceed(Text("Directory ", style=INSTALL_STYLE).append(str(install_dir), style='cyan').append(' does not exist. Create?'))
            install_dir.mkdir(parents=True)
            log_status(f"Created {install_dir.resolve()}")
        else:
            log_status(f"  -> Installing to: '{install_dir.resolve()}'\n", style='dim')

        for tool in PDF_TOOLS_FILES:
            tool_path = install_dir.joinpath(tool)
            tool_url = f"{DIDIER_STEVENS_RAW_GITHUB_URL}{tool}"
            log_status(f"Downloading '{tool}' from {tool_url}")
            response = requests.get(tool_url)
            tool_path.write_text(response.text)
            log_status(f"Making '{tool_path}' executable...")
            tool_path.chmod(os.stat(tool_path).st_mode | stat.S_IEXEC)

        log_console.print("\n\n\nDidier Stevens recommends always using the -O option with pdf-parser.py.")
        log_console.print("This can be accomplished by setting the PDFPARSER_OPTIONS environment variable:\n")
        log_console.print("         PDFPARSER_OPTIONS=-O\n")
        log_console.print("You are encouraged to add that to your environment via your .bash_profile or similar.")
        log_console.print("This has NOT been done automatically.")
