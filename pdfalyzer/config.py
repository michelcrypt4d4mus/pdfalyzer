import logging
from os import environ, path

from pdfalyzer.util.filesystem_awareness import PROJECT_DIR


PDFALYZE = 'pdfalyze'
PYTEST_FLAG = 'INVOKED_BY_PYTEST'

# Configuring PDFALYZER_LOG_DIR has side effects; see .pdfalyzer.example in repo for specifics.
LOG_LEVEL_ENV_VAR = 'PDFALYZER_LOG_LEVEL'
LOG_DIR_ENV_VAR = 'PDFALYZER_LOG_DIR'

# Output suppression
SUPPRESS_CHARDET_TABLE_ENV_VAR = 'PDFALYZER_SUPPRESS_CHARDET_TABLE'
SUPPRESS_DECODES_ENV_VAR = 'PDFALYZER_SUPPRESS_DECODE'

# Skip decoding binary matches over this length
DEFAULT_MIN_DECODE_LENGTH = 1
DEFAULT_MAX_DECODE_LENGTH = 256
MIN_DECODE_LENGTH_ENV_VAR = 'PDFALYZER_MIN_DECODE_LENGTH'
MAX_DECODE_LENGTH_ENV_VAR = 'PDFALYZER_MAX_DECODE_LENGTH'

# Number of bytes to show before/after byte previews and decodes. Configured by command line or env var
SURROUNDING_BYTES_LENGTH_DEFAULT = 64
SURROUNDING_BYTES_ENV_VAR = 'PDFALYZER_SURROUNDING_BYTES'

# 3rd part pdf-parser.py
PDF_PARSER_EXECUTABLE_ENV_VAR = 'PDFALYZER_PDF_PARSER_PY_PATH'


def is_env_var_set_and_not_false(var_name):
    """Returns True if var_name is not empty and set to anything other than 'false' (capitalization agnostic)"""
    if var_name in environ:
        var_value = environ[var_name]
        return var_value is not None and len(var_value) > 0 and var_value.lower() != 'false'
    else:
        return False


def is_invoked_by_pytest():
    """Return true if pytest is running"""
    return is_env_var_set_and_not_false(PYTEST_FLAG)


class PdfalyzerConfig:
    LOG_DIR = environ.get(LOG_DIR_ENV_VAR)
    LOG_LEVEL = logging.getLevelName(environ.get(LOG_LEVEL_ENV_VAR, 'WARN'))

    MIN_DECODE_LENGTH = int(environ.get(MIN_DECODE_LENGTH_ENV_VAR, DEFAULT_MIN_DECODE_LENGTH))
    MAX_DECODE_LENGTH = int(environ.get(MAX_DECODE_LENGTH_ENV_VAR, DEFAULT_MAX_DECODE_LENGTH))
    NUM_SURROUNDING_BYTES = int(environ.get(SURROUNDING_BYTES_ENV_VAR, SURROUNDING_BYTES_LENGTH_DEFAULT))
    SUPPRESS_CHARDET_OUTPUT = is_env_var_set_and_not_false(SUPPRESS_CHARDET_TABLE_ENV_VAR)
    SUPPRESS_DECODES = is_env_var_set_and_not_false(SUPPRESS_DECODES_ENV_VAR)

    JAVSCRIPT_KEYWORD_ALERT_THRESHOLD = 2
    QUOTE_TYPE = None

    # Path to Didier Stevens's pdf-parser.py
    if is_env_var_set_and_not_false(PDF_PARSER_EXECUTABLE_ENV_VAR):
        PDF_PARSER_EXECUTABLE = path.join(environ[PDF_PARSER_EXECUTABLE_ENV_VAR], 'pdf-parser.py')
    elif is_invoked_by_pytest():
        PDF_PARSER_EXECUTABLE = path.join(PROJECT_DIR, 'tools', 'pdf-parser.py')
    else:
        PDF_PARSER_EXECUTABLE = None
