"""
Python log levels:

    CRITICAL 50
    ERROR 40
    WARNING 30
    INFO 20
    DEBUG 10
    NOTSET 0
"""

import logging
from rich.logging import RichHandler


logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

log = logging.getLogger("rich")
