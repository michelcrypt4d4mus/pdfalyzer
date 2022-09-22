"""
Help with dicts
"""
from numbers import Number


def get_dict_key_by_value(_dict: dict, value):
    """Inverse of the usual dict operation"""
    return list(_dict.keys())[list(_dict.values()).index(value)]


def get_value_as_lowercase_and_none_if_blank(_dict: dict, key):
    """Return None if the value at :key is an empty string, empty list, etc."""
    value = _dict.get(key)

    if value is None or isinstance(value, Number):
        return value

    if isinstance(value, (dict, list, str)) and len(value) == 0:
        return None

    if isinstance(value, str):
        value = value.lower()

    return value
