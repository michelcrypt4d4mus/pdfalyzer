import os
import re
import stat
from argparse import Namespace
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

from rich.prompt import Confirm, Prompt
from rich.text import Text
from yaralyzer.util.helpers.env_helper import is_github_workflow, log_console, stderr_notification
from yaralyzer.util.exceptions import print_fatal_error_and_exit
from yaralyzer.util.helpers.interaction_helper import ask_to_proceed
from yaralyzer.util.helpers.shell_helper import ShellResult

from pdfalyzer.config import (CHECK_PDF_OCR_TEXT_PATH_ENV_VAR as CFG_CHECK_PDF_OCR_TEXT_PATH_ENV_VAR,
     PDF_PARSER_PATH_ENV_VAR as CFG_PDF_PARSER_PATH_ENV_VAR, PdfalyzerConfig)
from pdfalyzer.util.constants import CHECK_PDF_OCR_TEXT_URL, CONSIDER_INSTALLING_EXTRAS_MSG, PDF_PARSER_INSTALL_SCRIPT, PDF_PARSER_PY, PDFALYZER
from pdfalyzer.util.exceptions import PdfParserError
from pdfalyzer.util.helpers.filesystem_helper import DEFAULT_PDF_TOOLS_DIR, dir_str

# PDF Internal Data Regexes
CONTAINS_STREAM_REGEX = re.compile(r'\s+Contains stream$')
PDF_OBJECT_START_REGEX = re.compile(r'^obj (\d+) \d+$')

# check-pdf installation
CHECK_PDF_OCR_TEXT_PATH_ENV_VAR = PdfalyzerConfig.env_var_for_option_dest(CFG_CHECK_PDF_OCR_TEXT_PATH_ENV_VAR)

# Installation of pdf-parser.py info
DIDIER_STEVENS_RAW_GITHUB_URL = 'https://raw.githubusercontent.com/DidierStevens/DidierStevensSuite/master/'
PDF_PARSER_GITHUB_URL = DIDIER_STEVENS_RAW_GITHUB_URL + PDF_PARSER_PY
PDF_PARSER_PATH_ENV_VAR = PdfalyzerConfig.prefixed_env_var(CFG_PDF_PARSER_PATH_ENV_VAR)
PDF_TOOLS_FILES = [PDF_PARSER_PY, 'pdfid.py', 'xorsearch.py']

INSTALL_STYLE = 'light_cyan1'
INSTALL_STYLE_BOLD = f"{INSTALL_STYLE} bold"

INSTALL_DEFAULT_TXT = Text("(default: ", style='dim').append(f"./{DEFAULT_PDF_TOOLS_DIR}", style='cyan').append(')')
INSTALL_PROMPT = Text("\nWhere do you want to install PDF tools? ", style=INSTALL_STYLE_BOLD) + INSTALL_DEFAULT_TXT

TOOLS_INSTALL_MSG = f"If you need to install {PDF_PARSER_PY} it's a single .py file that can be " \
                    f"found at: {PDF_PARSER_GITHUB_URL}\n\nThere's also a script that comes with Pdfalyzer " \
                    f"that will install it for you if you run:\n\n    {PDF_PARSER_INSTALL_SCRIPT}\n\n"

POST_INSTALL_MSG = "\n\nDidier Stevens recommends always using the -O option with pdf-parser.py.\n" \
        "This can be accomplished by setting the PDFPARSER_OPTIONS environment variable:\n\n" \
        "         PDFPARSER_OPTIONS=-O\n\n" \
        "You are encouraged to add that to your environment via your .bash_profile or similar.\n" \
        "This has NOT been done automatically."

log = PdfalyzerConfig.log


@dataclass
class PdfParserManager:
    """Manage external calls to Didier Stevens's pdf-parser.py."""
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
            log.debug(result.output_logs())
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
        stderr_notification(f"\nExtracting binary streams in '{self.path_to_pdf}' to files in '{output_dir_str}'...")
        files_written = []

        for object_id in self.object_ids_containing_stream_data:
            stream_dump_file = self.output_dir.joinpath(f'{self.path_to_pdf.name}.object_{object_id}.bin')
            shell_cmd = self.base_shell_cmd + ['-f', '-o', object_id, '-d', stream_dump_file]
            log.info(f'Dumping stream from object {object_id} with cmd:\n\n{shell_cmd}\n')

            try:
                ShellResult.from_cmd(shell_cmd, verify_success=True)
                files_written.append(stream_dump_file)
            except Exception as e:
                log.error(f"Failed to extract object ID {object_id}! {e}")

        stderr_notification(f"{len(files_written)} extracted binary streams were written to {output_dir_str}.")
        num_failures = len(self.object_ids_containing_stream_data) - len(files_written)

        if num_failures > 0:
            log_console.print(f"{num_failures} streams could not be extracted!", style='bright_red')

    @staticmethod
    def install_didier_stevens_tools() -> None:
        """Get Didier Stevens's pdf-parser.py and pdfid.py from github."""
        try:
            import requests
        except ModuleNotFoundError:
            print_fatal_error_and_exit(f"'requests' package not installed. {CONSIDER_INSTALLING_EXTRAS_MSG.plain}")

        # Skip confirmation if env var is set (used by Github workflows)
        if is_github_workflow():
            install_dir = DEFAULT_PDF_TOOLS_DIR
        else:
            install_dir = Prompt.ask(INSTALL_PROMPT, default=DEFAULT_PDF_TOOLS_DIR, show_default=False)
            install_dir = Path(install_dir)

            if not install_dir.exists():
                ask_to_proceed(Text(f"Directory {install_dir.resolve()} does not exist. Create?", style=INSTALL_STYLE))

        if not install_dir.exists():
            install_dir.mkdir(exist_ok=True, parents=True)
            log_install_step(f"Created {install_dir.resolve()}")
        else:
            log_install_step(f"Installing to existing dir {install_dir.resolve()}")

        for tool in PDF_TOOLS_FILES:
            tool_url = f"{DIDIER_STEVENS_RAW_GITHUB_URL}{tool}"
            PdfParserManager.install_python_tool(install_dir, tool_url)

        installed_pdf_parser_path = install_dir.joinpath(PDF_PARSER_PY).resolve()
        pdfalyzer_cfg_line = f'{PDF_PARSER_PATH_ENV_VAR}="{installed_pdf_parser_path}"'

        check_ocr_path = PdfParserManager.install_python_tool(install_dir, CHECK_PDF_OCR_TEXT_URL).resolve()
        check_pdf_ocr_text_line = f'{CHECK_PDF_OCR_TEXT_PATH_ENV_VAR}="{check_ocr_path}"'
        dotfile_write_txt = Text(f"Write ", style=INSTALL_STYLE)
        dotfile_write_txt.append(pdfalyzer_cfg_line, style='cyan').append(' to ')
        dotfile_write_txt.append(PdfalyzerConfig.dotfile_name, style='cyan').append('?')

        log_install_msg(
            f"\nYou chose to install {PDF_PARSER_PY} to {installed_pdf_parser_path}.\n"
            f"In order for {PDFALYZER} to use it to verify PDF objects you can write this location "
            f"to a {PdfalyzerConfig.dotfile_name} file.\n"
        )

        if not is_github_workflow() and Confirm.ask(dotfile_write_txt):
            dotfile_path = Path(PdfalyzerConfig.dotfile_name)

            with open(dotfile_path, 'at') as dotfile:
                dotfile.write(f'\n{pdfalyzer_cfg_line}\n{check_pdf_ocr_text_line}\n')

            log_install_step(f"Wrote line to {dotfile_path.resolve()}")

        log_install_msg(POST_INSTALL_MSG, style='dim')

    @staticmethod
    def install_python_tool(install_dir: Path, tool_url: str) -> Path:
        import requests
        tool = tool_url.split('/')[-1]
        tool_path = install_dir.joinpath(tool)
        log_install_step(f"Downloading '{tool}' from {tool_url}")
        response = requests.get(tool_url)
        tool_path.write_text(response.text)
        log_install_step(f"Making '{tool_path}' executable...")
        tool_path.chmod(os.stat(tool_path).st_mode | stat.S_IEXEC)
        return tool_path


def log_install_step(msg, **kwargs) -> None:
    log_install_msg(f"  -> {msg}", style='gray27', **kwargs)


def log_install_msg(msg, **kwargs) -> None:
    style = kwargs.pop('style') if 'style' in kwargs else INSTALL_STYLE
    log_console.print(msg, style=style, **kwargs)
