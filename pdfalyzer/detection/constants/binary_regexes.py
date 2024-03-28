"""
Configuration of what to scan for in binary data. Regexes here will be matched against binary streams
and then force decoded.
"""
from pdfalyzer.util.adobe_strings import DANGEROUS_PDF_KEYS

DANGEROUS_JAVASCRIPT_INSTRUCTIONS = ['eval']
DANGEROUS_PDF_KEYS_TO_HUNT_WITH_SLASH = ['/URI']
DANGEROUS_PDF_KEYS_TO_HUNT_ONLY_IN_FONTS = ['/AA', '/F']

HEX_ENCODED_PDF_KEYS_TO_HUNT = [
    '/#55#52#49',  # URI
]

# Potentially dangerous PDF instructions: Remove the leading '/' and convert to bytes except /F ("URL")
DANGEROUS_STRINGS = [instruction[1:] for instruction in DANGEROUS_PDF_KEYS]
DANGEROUS_STRINGS.extend(DANGEROUS_PDF_KEYS_TO_HUNT_WITH_SLASH)
DANGEROUS_STRINGS.extend(DANGEROUS_JAVASCRIPT_INSTRUCTIONS)

# Quote capture regexes
DOUBLE_QUOTE = 'double_quote'
SINGLE_QUOTE = 'single_quote'

BACKSLASH = 'backslash'
BACKTICK = 'backtick'
BRACKET = 'bracket'
CURLY_BRACKET = 'curly_bracket'
DOUBLE_LESS_THAN = 'double_lessthan'
ESCAPED_SINGLE = f"escaped_{SINGLE_QUOTE}"
ESCAPED_DOUBLE = f"escaped_{DOUBLE_QUOTE}"
FRONTSLASH = 'frontslash'
GUILLEMET = 'guillemet'
LESS_THAN = 'lessthan'
PARENTHESES = 'parentheses'


QUOTE_PATTERNS = {
    BACKTICK: '`.+`',
    BRACKET: '\\[.+\\]',  # { 91 [-] 93 }
    CURLY_BRACKET: '{.+}',  # { 123 [-] 125 }
    DOUBLE_LESS_THAN: '<<.+>>', # Hex { 60 60 [-] 62 62 }
    ESCAPED_SINGLE: "\\'.+\\'",
    ESCAPED_DOUBLE: '\\".+\\"',
    FRONTSLASH: '/.+/',  # { 47 [-] 47 }
    GUILLEMET: 'AB [-] BB',  # Guillemet quotes are not ANSI so require byte pattern
    LESS_THAN: '<.+>',  # Hex { 60 [-] 62 }
    PARENTHESES: '\\(.+\\)', # Hex { 28 [-] 29 }
}
