"""
Instances of this class manage external calls to Didier Stevens's pdf-parser.py for a given PDF.
"""
from os import path, system
from subprocess import check_output
import pathlib
import re

from lib.util.logging import log


PROJECT_DIR = path.join(pathlib.Path(__file__).parent.resolve(), '..')
PDF_PARSER_EXECUTABLE = path.join(PROJECT_DIR, 'tools', 'pdf-parser.py')

PDF_OBJECT_START_REGEX = re.compile('^obj (\d+) \d+$')
CONTAINS_STREAM_REGEX = re.compile('\s+Contains stream$')


class PdfParserManager:
    def __init__(self, path_to_pdf):
        if not path.exists(PDF_PARSER_EXECUTABLE):
            raise RuntimeError(f"pdf-parser.py not found. Install it with 'scripts/install_didier_stevens_pdf_tools.sh'")

        self.path_to_pdf = path_to_pdf
        self.base_shell_cmd = f'{PDF_PARSER_EXECUTABLE} -O "{path_to_pdf}"'

    def object_ids_containing_stream_data(self):
        """Use pdf-parser.py to find IDs of objects in self.path_to_pdf containing stream data"""
        log.debug(f"Running '{self.base_shell_cmd}'")
        pdf_parser_output = check_output(self.base_shell_cmd, shell=True, text=True)
        object_ids_with_streams = []
        current_object_id = None

        for line in pdf_parser_output.split("\n"):
            match = PDF_OBJECT_START_REGEX.match(line)

            if match:
                current_object_id = match[1]

            if current_object_id is None:
                continue

            if CONTAINS_STREAM_REGEX.match(line):
                log.debug(f"{current_object_id} contains a stream!")
                object_ids_with_streams.append(int(current_object_id))

        log.info(f"{self.path_to_pdf} Object IDs with streams: {object_ids_with_streams}")
        return object_ids_with_streams

    def extract_all_streams(self, output_dir):
        """Use pdf-parser.py to find binary data streams in the PDF and dump each of them to a separate file"""
        for object_id in self.object_ids_containing_stream_data():
            stream_dump_file = path.join(output_dir, f'{path.basename(self.path_to_pdf)}.object_{object_id}.dump')
            shell_cmd = self.base_shell_cmd + f' -f -o {object_id} -d "{stream_dump_file}"'
            log.debug(f'Dumping stream from object {object_id}: {shell_cmd}')
            system(shell_cmd)
