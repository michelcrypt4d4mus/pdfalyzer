"""
Configuration of what to scan for in binary data. Regexes here will be matched against binary streams
and then force decoded
"""

import re
from typing import Union

from pdfalyzer.util.adobe_strings import DANGEROUS_PDF_KEYS
from pdfalyzer.detection.constants.character_encodings import BOMS


# Potentially dangerous PDF instructions: Remove the leading '/' and convert to bytes except /F ("URL")
DANGEROUS_BYTES = [instruction[1:].encode() for instruction in DANGEROUS_PDF_KEYS] + [b'/F']
DANGEROUS_JAVASCRIPT_INSTRUCTIONS = [b'eval']
DANGEROUS_INSTRUCTIONS = DANGEROUS_BYTES + DANGEROUS_JAVASCRIPT_INSTRUCTIONS + list(BOMS.keys())

# Quote capture regexes
CAPTURE_BYTES = b'(.*?)'
FRONT_SLASH_BYTE = b"/"
ESCAPED_DOUBLE_QUOTE_BYTES = b'\\"'
ESCAPED_SINGLE_QUOTE_BYTES = b"\\'"


# Quote regexes used to hunt for particular binary patterns of interest
def build_quote_capture_group(open_quote: bytes, close_quote: Union[bytes, None]=None):
    """Regex that captures everything between open and close quote (close_quote defaults to open_quote)"""
    return re.compile(open_quote + CAPTURE_BYTES + (close_quote or open_quote), re.DOTALL)


QUOTE_REGEXES = {
    'backtick': build_quote_capture_group(b'`'),
    'guillemet': build_quote_capture_group(b'\xab', b'\xbb'),
    'escaped_single': build_quote_capture_group(ESCAPED_SINGLE_QUOTE_BYTES),
    'escaped_double': build_quote_capture_group(ESCAPED_DOUBLE_QUOTE_BYTES),
    'frontslash': build_quote_capture_group(FRONT_SLASH_BYTE),
}
