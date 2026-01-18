"""
Fun with dicts.
"""
from pypdf.generic import ArrayObject, DictionaryObject
from yaralyzer.util.logging import log


without_nones = lambda _list: [e for e in _list if e]


def get_dict_key_by_value(_dict: dict, value):
    """Inverse of the usual dict operation"""
    return list(_dict.keys())[list(_dict.values()).index(value)]


def merge(dict1: dict, dict2: dict) -> dict:
    """Merge two dicts into a new dict"""
    return {**dict1, **dict2}


def compare_dicts(d1: DictionaryObject, d2: DictionaryObject, already_compared_keys: list[str] | None = None) -> None:
    should_call_again = already_compared_keys is None
    already_compared_keys = already_compared_keys or []

    for k, v in d1.items():
        if k in already_compared_keys or k == '/FontDescriptor':
            continue
        elif k not in d2:
            log.warning(f"'{k}' is not in dict2")
        elif v != d2[k]:
            print('')
            log.warning(f"'{k}' has different values.\n    d1['{k}']: {v}\n    d2['{k}']: {d2[k]}\n")

        already_compared_keys.append(k)

    # call with reversed args
    if should_call_again:
        compare_dicts(d2, d1, already_compared_keys)
