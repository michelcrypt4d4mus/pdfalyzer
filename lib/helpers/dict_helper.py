"""
Help with dicts
"""
from numbers import Number
from os import environ


def get_dict_key_by_value(_dict: dict, value):
    """Inverse of the usual dict operation"""
    return list(_dict.keys())[list(_dict.values()).index(value)]


def get_lowercase_value(_dict: dict, key):
    """Return None if the value at :key is an empty string, empty list, etc."""
    value = _dict.get(key)

    if value is None or isinstance(value, Number):
        return value
    elif isinstance(value, (dict, list, str)) and len(value) == 0:
        return None
    elif isinstance(value, str):
        value = value.lower()

    return value


def is_env_var_set_and_not_false(var_name):
    """Returns True if var_name is not empty and set to anything other than 'false' (capitalization agnostic)"""
    if var_name in environ:
        var_value = environ[var_name]
        return len(var_value) > 0 and var_value.lower() != 'false'
    else:
        return False
