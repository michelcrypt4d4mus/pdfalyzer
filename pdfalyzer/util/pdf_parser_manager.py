"""
Instances of this class manage external calls to Didier Stevens's pdf-parser.py for a given PDF.
"""
import re
from os import path, system
from subprocess import check_output

from yaralyzer.util.logging import log

from pdfalyzer.config import PDF_PARSER_EXECUTABLE_ENV_VAR, PdfalyzerConfig
from pdfalyzer.util.filesystem_awareness import PROJECT_DIR

# PDF Internal Data Regexes
PDF_OBJECT_START_REGEX = re.compile('^obj (\\d+) \\d+$')
CONTAINS_STREAM_REGEX = re.compile('\\s+Contains stream$')

# Install info
DIDIER_STEVENS_RAW_GITHUB_URL = 'https://raw.githubusercontent.com/DidierStevens/DidierStevensSuite/master/'
PDF_PARSER_GITHUB_URL = DIDIER_STEVENS_RAW_GITHUB_URL + 'pdf-parser.py'
PDF_PARSER_INSTALL_MSG = f"If you need to install pdf-parser.py, it's a single .py file that can be " + \
                          "found at '{PDF_PARSER_GITHUB_URL}'."


class PdfParserManager:
    def __init__(self, path_to_pdf):
        if PdfalyzerConfig.PDF_PARSER_EXECUTABLE is None:
            raise RuntimeError(f"{PDF_PARSER_EXECUTABLE_ENV_VAR} not configured.\n\n{PDF_PARSER_INSTALL_MSG}")

        if not path.exists(PdfalyzerConfig.PDF_PARSER_EXECUTABLE):
            msg = f"pdf-parser.py not found at configured location '{PdfalyzerConfig.PDF_PARSER_EXECUTABLE}'\n\n"
            msg += PDF_PARSER_INSTALL_MSG
            raise RuntimeError(msg)

        self.path_to_pdf = path_to_pdf
        self.base_shell_cmd = f'{PdfalyzerConfig.PDF_PARSER_EXECUTABLE} -O "{path_to_pdf}"'
        self.object_ids = []
        self.object_ids_containing_stream_data = []
        self.extract_object_ids()

    def extract_object_ids(self):
        """Examine output of pdf-parser.py to find all object IDs as well as those object IDs that have streams"""
        log.debug(f"Running '{self.base_shell_cmd}'")
        self.pdf_parser_output_lines = check_output(self.base_shell_cmd, shell=True, text=True).split("\n")
        current_object_id = None

        for line in self.pdf_parser_output_lines:
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

    def extract_all_streams(self, output_dir):
        """Use pdf-parser.py to find binary data streams in the PDF and dump each of them to a separate file"""
        for object_id in self.object_ids_containing_stream_data:
            stream_dump_file = path.join(output_dir, f'{path.basename(self.path_to_pdf)}.object_{object_id}.bin')
            shell_cmd = self.base_shell_cmd + f' -f -o {object_id} -d "{stream_dump_file}"'
            log.debug(f'Dumping stream from object {object_id}: {shell_cmd}')
            system(shell_cmd)
