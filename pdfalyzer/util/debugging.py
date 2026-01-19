import logging

from yaralyzer.util.logging import log


def log_trace(*args) -> None:
    """Log below logging.DEBUG level."""
    log.log(logging.DEBUG - 1, *args)
