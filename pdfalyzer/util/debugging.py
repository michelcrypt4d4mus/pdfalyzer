import logging

import pypdf
from rich.console import Console
from rich.logging import RichHandler

from yaralyzer.util.logging import log


# Redirect pypdf logs
pypdf_logger = logging.getLogger("pypdf")
log_console = Console(stderr=True)
pypdf_log_handler = RichHandler(console=log_console, rich_tracebacks=True)
pypdf_log_handler.setLevel(logging.WARNING)
pypdf_log_handler.formatter = logging.Formatter('[pypdf] %(message)s')
pypdf_logger.addHandler(pypdf_log_handler)
# pypdf_logger.warning(f"This is a pypddf warning, formatter is {pypdf_log_handler.formatter}")


def log_trace(*args) -> None:
    """Log below logging.DEBUG level."""
    log.log(logging.DEBUG - 1, *args)
