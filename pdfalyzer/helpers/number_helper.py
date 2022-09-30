from numbers import Number
from typing import Union

from pdfalyzer.util.logging import log


def is_divisible_by(n: Union[Number, int], divisor: Union[Number, int]) -> bool:
    return divmod(n, divisor)[1] == 0


def is_even(n: Number) -> bool:
    return is_divisible_by(n, 2)
