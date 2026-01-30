"""
Helper methods for dealing with lists and dicts.
"""
import json

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


def prefix_keys(prefix: str, _dict: dict[str, str]) -> dict[str, str]:
    """Add `prefix` to the front of all the keys in `_dict`."""
    return {f"{prefix}{k}": v for k, v in _dict.items()}


def safe_json(obj: object) -> str:
    return json.dumps(stringify_props(obj), indent=4)


def stringify_props(obj: object) -> object:
    """Make `obj` safe for JSON export."""
    if isinstance(obj, list):
        return [stringify_props(element) for element in obj]
    elif isinstance(obj, dict):
        return {str(k): stringify_props(v) for k, v in obj.items()}
    elif '__dict__' in dir(obj):
        return {str(k): stringify_props(v) for k, v in vars(obj).items()}
    elif isinstance(obj, (float, int, str)):
        return obj
    else:
        try:
            return json.dumps(obj)
        except Exception:
            return str(obj)


def without_falsey(_list: list) -> list:
    """Return `_list` without falsey elements (None, empty string, empty dict/list)."""
    return [e for e in _list if e]
