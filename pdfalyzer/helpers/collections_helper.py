"""
Helper methods for dealing with lists and dicts.
"""
from pypdf.generic import DictionaryObject
from yaralyzer.util.logging import log


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


def without_falsey(_list: list) -> list:
    return [e for e in _list if e]
