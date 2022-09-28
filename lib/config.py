import logging
from os import environ


LOG_LEVEL_ENV_VAR = 'PDFALYZER_LOG_LEVEL'

# Output suppression
SUPPRESS_CHARDET_TABLE_ENV_VAR = 'PDFALYZER_SUPPRESS_CHARDET_TABLE'
SUPPRESS_DECODES_ENV_VAR = 'PDFALYZER_SUPPRESS_DECODE'

# Skip decoding binary matches over this length
DEFAULT_MAX_DECODABLE_CHUNK_SIZE = 256
MAX_DECODABLE_CHUNK_SIZE_ENV_VAR = 'PDFALYZER_MAX_DECODABLE_CHUNK_SIZE'

# Number of bytes to show before/after byte previews and decodes. Configured by command line or env var
SURROUNDING_BYTES_LENGTH_DEFAULT = 64
SURROUNDING_BYTES_ENV_VAR = 'PDFALYZER_SURROUNDING_BYTES'


def is_env_var_set_and_not_false(var_name):
    """Returns True if var_name is not empty and set to anything other than 'false' (capitalization agnostic)"""
    if var_name in environ:
        var_value = environ[var_name]
        return len(var_value) > 0 and var_value.lower() != 'false'
    else:
        return False


class PdfalyzerConfig:
    log_level = getattr(logging, environ.get(LOG_LEVEL_ENV_VAR, 'DEBUG'))
    max_decodable_chunk_size = int(environ.get(MAX_DECODABLE_CHUNK_SIZE_ENV_VAR, DEFAULT_MAX_DECODABLE_CHUNK_SIZE))
    num_surrounding_bytes = int(environ.get(SURROUNDING_BYTES_ENV_VAR, SURROUNDING_BYTES_LENGTH_DEFAULT))
    suppress_chardet_output = is_env_var_set_and_not_false(SUPPRESS_CHARDET_TABLE_ENV_VAR)
    suppress_decodes = is_env_var_set_and_not_false(SUPPRESS_DECODES_ENV_VAR)
