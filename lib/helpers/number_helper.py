from numbers import Number
from lib.util.logging import log


def is_even(n: Number) -> bool:
    if not isinstance(int):
        log.warning(f"Non ints like {n} are never even")
        return False

    return divmod(n, 2)[1] == 0

