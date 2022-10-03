import re
from collections import namedtuple
from numbers import Number
from os import path
from typing import Any, Dict, List, Union
from pdfalyzer.binary.bytes_match import BytesMatch

import yara
from rich.padding import Padding
from rich.text import Text

from pdfalyzer.binary.bytes_decoder import BytesDecoder
from pdfalyzer.detection.constants.javascript_reserved_keywords import HIGH_VALUE_KEYWORDS
from pdfalyzer.helpers.bytes_helper import clean_byte_string
from pdfalyzer.helpers.file_helper import load_binary_data
from pdfalyzer.helpers.rich_text_helper import console, console_width, dim_if
from pdfalyzer.util.filesystem_awareness import PROJECT_DIR
from pdfalyzer.util.logging import log

# Some rules are applied to the whole file, others we only want to apply to decrypted/decoded binary streams
YARA_RULE_DIR = path.join(PROJECT_DIR, 'yara')
YARA_PDF_RULES_FILE = path.join(YARA_RULE_DIR, 'PDF.yara')
YARA_STREAM_RULES_FILE = path.join(YARA_RULE_DIR, 'PDF_binary_stream.yara')
YARA_PDF_RULES = yara.compile(YARA_PDF_RULES_FILE)
YARA_STREAM_RULES = yara.compile(YARA_STREAM_RULES_FILE)

URL_REGEX = re.compile('^https?:')
DIGITS_REGEX = re.compile("^\\d+$")
HEX_REGEX = re.compile('^[0-9A-Fa-f]+$')
DATE_REGEX = re.compile('\\d{4}-\\d{2}-\\d{2}')
MATCHER_VAR_REGEX = re.compile('\\$[a-z_]+')

YARA_STRING_STYLES: Dict[re.Pattern, str] = {
    URL_REGEX: 'yara.url',
    DIGITS_REGEX: 'yara.number',
    HEX_REGEX: 'yara.hex',
    DATE_REGEX: 'yara.date',
    MATCHER_VAR_REGEX: 'yara.match_var'
}

YaraResults = namedtuple('YaraResults', ['matches', 'non_matches'])


class YaraScanner:
    def __init__(self, _bytes: bytes, label: Union[str, Text]) -> None:
        self.bytes: bytes = _bytes
        self.label: Text = Text(label) if isinstance(label, str) else label
        self.matches = []
        self.non_matches = []

    @classmethod
    def for_file(cls, file_path: str) -> 'YaraScanner':
        """Load the binary data from file_path"""
        return cls(load_binary_data(file_path), path.basename(file_path))

    def scan(self) -> None:
        def yara_callback(data: dict):
            if data['matches']:
                self.matches.append(data)
            else:
                self.non_matches.append(data)

            return yara.CALLBACK_CONTINUE

        YARA_PDF_RULES.match(data=self.bytes, callback=yara_callback)
        YARA_STREAM_RULES.match(data=self.bytes, callback=yara_callback)
        self.any_matches = (len(self.matches) > 0)

        for yara_match in self.matches:
            console.print(self.label + Text(f" matched yara rule '{yara_match['rule']}'!", style='error'))
            console.print(rich_yara_match(yara_match))
            console.line()

            for match in BytesMatch.for_yara_strings_in_match(self.bytes, yara_match):
                BytesDecoder(match, yara_match['rule']).print_decode_attempts()

        non_matches_text = sorted([Text(nm['rule'], 'grey') for nm in self.non_matches], key=str)

        # Only show the non matches if there were valid ones, otherwise just show the number
        if self.any_matches:
            non_match_desc = f" did not match the other {len(self.non_matches)} yara rules"
            console.print(self.label + Text(non_match_desc, style='grey.dark') + Text(': '))
            console.print(Padding(Text(', ', 'white').join(non_matches_text), (0, 0, 1, 4)))
        else:
            non_match_desc = f" did not match any of the {len(self.non_matches)} yara rules"
            console.print(dim_if(self.label + Text(non_match_desc, style='grey.dark'), True))


def rich_yara_match(element: Any, depth: int = 0) -> Text:
    """Mildly painful/hacky way of coloring a yara result hash"""
    indent = Text((depth + 1) * 4 * ' ')
    end_indent = Text(depth * 4 * ' ')

    if isinstance(element, str):
        txt = yara_string(element)
    elif isinstance(element, bytes):
        txt = Text(clean_byte_string(element), style='bytes')
    elif isinstance(element, Number):
        txt = Text(str(element), style='bright_cyan')
    elif isinstance(element, bool):
        txt = Text(str(element), style='red' if not element else 'green')
    elif isinstance(element, (list, tuple)):
        if len(element) == 0:
            txt = Text('[]', style='white')
        else:
            total_length = sum([len(str(e)) for e in element]) + ((len(element) - 1) * 2) + + len(indent) + 2
            elements_txt = [rich_yara_match(e, depth + 1) for e in element]
            list_txt = Text('[', style='white')

            if total_length > console_width() or len(element) > 3:
                join_txt = Text(f"\n{indent}" )
                list_txt.append(join_txt).append(Text(f",{join_txt}").join(elements_txt))
                list_txt += Text(f'\n{end_indent}]', style='white')
            else:
                list_txt += Text(', ').join(elements_txt) + Text(']')

            return list_txt
    elif isinstance(element, dict):
        element = {k: v for k, v in element.items() if k not in ['matches', 'rule']}

        if len(element) == 0:
            return Text('{}')

        txt = Text('{\n', style='white')

        for i, k in enumerate(element.keys()):
            v = element[k]
            txt += indent + Text(f"{k}: ", style='yara.key') + rich_yara_match(v, depth + 1)

            if (i + 1) < len(element.keys()):
                txt.append(",\n")
            else:
                txt.append("\n")

        txt += end_indent + Text('}', style='white')
    else:
        log.warn(f"Unknown yara return of type {type(element)}: {element}")
        txt = indent + Text(str(element))

    return txt


def yara_string(_string: str) -> Text:
    for regex in YARA_STRING_STYLES.keys():
        if regex.match(_string):
            return Text(_string, YARA_STRING_STYLES[regex])

    return Text(_string, style='yara.string')
