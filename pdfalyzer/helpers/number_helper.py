from numbers import Number
from typing import Union

from rich.text import Text


def is_divisible_by(n: int, divisor: int) -> bool:
    return divmod(n, divisor)[1] == 0


def is_even(n: int) -> bool:
    return is_divisible_by(n, 2)
