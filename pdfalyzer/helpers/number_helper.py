from numbers import Number
from typing import Union

from rich.text import Text

from yaralyzer.helpers.rich_text_helper import prefix_with_plain_text_obj


def is_divisible_by(n: int, divisor: int) -> bool:
    return divmod(n, divisor)[1] == 0


def is_even(n: int) -> bool:
    return is_divisible_by(n, 2)


def size_string(num_bytes: int) -> Text:
    """Convert a number of bytes into (e.g.) 54,213 bytes (52 KB)"""
    kb_txt = prefix_with_plain_text_obj("{:,.1f}".format(num_bytes / 1024), style='bright_cyan', root_style='white')
    kb_txt.append(' kb ')
    bytes_txt = Text('(', 'white') + size_in_bytes_string(num_bytes) + Text(')')

    return kb_txt + bytes_txt


def size_in_bytes_string(num_bytes: int) -> Text:
    return  Text(f"{num_bytes:,d}", 'number').append(' bytes', style='white')
