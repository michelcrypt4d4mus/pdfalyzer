import logging
from os import environ

from lib.util.filesystem_awareness import DEFAULT_LOG_DIR


# Configuring PDFALYZER_LOG_DIR has side effects; see .env.example in repo for specifics.
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


def is_env_var_set_and_not_false(var_name):
    """Returns True if var_name is not empty and set to anything other than 'false' (capitalization agnostic)"""
    if var_name in environ:
        var_value = environ[var_name]
        return var_value is not None and len(var_value) > 0 and var_value.lower() != 'false'
    else:
        return False


class PdfalyzerConfig:
    LOG_DIR = environ.get(LOG_DIR_ENV_VAR, DEFAULT_LOG_DIR)
    LOG_LEVEL = getattr(logging, environ.get(LOG_LEVEL_ENV_VAR, 'DEBUG'))
    IS_LOGGING_TO_FILE = is_env_var_set_and_not_false(LOG_DIR_ENV_VAR)
    WAS_LOG_LEVEL_CONFIGURED = is_env_var_set_and_not_false(LOG_LEVEL_ENV_VAR)

    MIN_DECODE_LENGTH = int(environ.get(MIN_DECODE_LENGTH_ENV_VAR, DEFAULT_MIN_DECODE_LENGTH))
    MAX_DECODE_LENGTH = int(environ.get(MAX_DECODE_LENGTH_ENV_VAR, DEFAULT_MAX_DECODE_LENGTH))
    NUM_SURROUNDING_BYTES = int(environ.get(SURROUNDING_BYTES_ENV_VAR, SURROUNDING_BYTES_LENGTH_DEFAULT))
    SUPPRESS_CHARDET_OUTPUT = is_env_var_set_and_not_false(SUPPRESS_CHARDET_TABLE_ENV_VAR)
    SUPPRESS_DECODES = is_env_var_set_and_not_false(SUPPRESS_DECODES_ENV_VAR)
