from numbers import Number
from typing import Union

from rich.text import Text

from yaralyzer.helpers.rich_text_helper import prefix_with_plain_text_obj


def is_divisible_by(n: int, divisor: int) -> bool:
    return divmod(n, divisor)[1] == 0


def is_even(n: Number) -> bool:
    return is_divisible_by(n, 2)


def size_string(num_bytes: int) -> Text:
    """Convert a number of bytes into (e.g.) 54,213 bytes (52 KB)"""
    txt = prefix_with_plain_text_obj(f"{num_bytes:,d}", 'number', root_style='white').append(' bytes ')
    kb_text = Text('(', style='white').append("{:,.1f}".format(num_bytes / 1024), style='grey')
    return txt + kb_text.append(' KB', 'white').append(")")

