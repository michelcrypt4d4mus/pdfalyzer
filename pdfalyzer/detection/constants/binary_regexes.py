"""
Configuration of what to scan for in binary data. Regexes here will be matched against binary streams
and then force decoded
"""

import re
from typing import Union

from deprecated import deprecated

from pdfalyzer.util.adobe_strings import DANGEROUS_PDF_KEYS

DANGEROUS_JAVASCRIPT_INSTRUCTIONS = ['eval']
DANGEROUS_PDF_KEYS_TO_HUNT_WITH_SLASH = ['/F', '/AA']

# Potentially dangerous PDF instructions: Remove the leading '/' and convert to bytes except /F ("URL")
DANGEROUS_STRINGS = [instruction[1:] for instruction in DANGEROUS_PDF_KEYS]
DANGEROUS_STRINGS.extend(DANGEROUS_PDF_KEYS_TO_HUNT_WITH_SLASH)
DANGEROUS_STRINGS.extend(DANGEROUS_JAVASCRIPT_INSTRUCTIONS)

# Quote capture regexes
GUILLEMET = 'guillemet'
FRONTSLASH = 'frontslash'
BACKSLASH = 'backslash'
BACKTICK = 'backtick'
SINGLE_QUOTE = 'single_quote'
DOUBLE_QUOTE = 'double_quote'
ESCAPED_SINGLE = f"escaped_{SINGLE_QUOTE}"
ESCAPED_DOUBLE = f"escaped_{DOUBLE_QUOTE}"

QUOTE_PATTERNS = {
    BACKTICK: '`.+`',
    ESCAPED_SINGLE: "\\'.+\\'",
    ESCAPED_DOUBLE: '\\".+\\"',
    FRONTSLASH: '/.+/',
    GUILLEMET: 'AB [-] BB',  # Guillemet quotes are not ANSI so require byte pattern
}
