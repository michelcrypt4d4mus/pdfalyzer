"""
Fun with dicts.
"""

without_nones = lambda _list: [e for e in _list if e]


def get_dict_key_by_value(_dict: dict, value):
    """Inverse of the usual dict operation"""
    return list(_dict.keys())[list(_dict.values()).index(value)]


def merge(dict1: dict, dict2: dict) -> dict:
    """Merge two dicts into a new dict"""
    return {**dict1, **dict2}
