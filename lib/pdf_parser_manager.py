"""
Instances of this class manage external calls to Didier Stevens's pdf-parser.py for a given PDF.
"""
import re
from os import path, system
from subprocess import check_output

from lib.util.filesystem_awareness import PROJECT_DIR
from lib.util.logging import log

# PDF Internal Data Regexes
PDF_OBJECT_START_REGEX = re.compile('^obj (\d+) \d+$')
CONTAINS_STREAM_REGEX = re.compile('\s+Contains stream$')
PDF_PARSER_EXECUTABLE = path.join(PROJECT_DIR, 'tools', 'pdf-parser.py')


class PdfParserManager:
    def __init__(self, path_to_pdf):
        if not path.exists(PDF_PARSER_EXECUTABLE):
            raise RuntimeError(f"pdf-parser.py not found. Install it with 'scripts/install_didier_stevens_pdf_tools.sh'")

        self.path_to_pdf = path_to_pdf
        self.base_shell_cmd = f'{PDF_PARSER_EXECUTABLE} -O "{path_to_pdf}"'
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
            stream_dump_file = path.join(output_dir, f'{path.basename(self.path_to_pdf)}.object_{object_id}.dump')
            shell_cmd = self.base_shell_cmd + f' -f -o {object_id} -d "{stream_dump_file}"'
            log.debug(f'Dumping stream from object {object_id}: {shell_cmd}')
            system(shell_cmd)
