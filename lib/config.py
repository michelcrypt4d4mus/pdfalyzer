from os import environ

SURROUNDING_BYTES_ENV_VAR = 'PDFALYZER_SURROUNDING_BYTES'
SURROUNDING_BYTES_LENGTH_DEFAULT = 64
SUPPRESS_CHARDET_TABLE_ENV_VAR = 'PDFALYZER_SUPPRESS_CHARDET_TABLE'
LOG_LEVEL_ENV_VAR = 'PDFALYZER_LOG_LEVEL'


def num_surrounding_bytes():
    """Number of bytes to show before/after byte previews and decodes. Configured by command line or env var"""
    return int(environ.get(SURROUNDING_BYTES_ENV_VAR, SURROUNDING_BYTES_LENGTH_DEFAULT))


def is_env_var_set_and_not_false(var_name):
    """Returns True if var_name is not empty and set to anything other than 'false' (capitalization agnostic)"""
    if var_name in environ:
        var_value = environ[var_name]
        return len(var_value) > 0 and var_value.lower() != 'false'
    else:
        return False


class PdfalyzerConfig:
    suppress_chardet_output = is_env_var_set_and_not_false(SUPPRESS_CHARDET_TABLE_ENV_VAR)
