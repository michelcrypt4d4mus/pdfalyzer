"""
Log formatting and redirection. This file yields a lot of pypdf warnings:
    pdfalyze ../pypdf/tests/pdf_cache/iss2812.pdf
"""
import logging

import pypdf
from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.logging import RichHandler
from rich.theme import Theme

from yaralyzer.util.logging import log, log_console

LOG_THEME_DICT = {
    "pypdf_prefix": "light_slate_gray",
    "pypdf_line": "dim",
}

LOG_THEME = Theme({f"{ReprHighlighter.base_style}{k}": v for k,v in LOG_THEME_DICT.items()})
PYPDF_LOG_PREFIX = r"\(pypdf\)"


# Augment the standard log highlighter
class LogHighlighter(ReprHighlighter):
    highlights = ReprHighlighter.highlights + [
        fr"(?P<pypdf_prefix>{PYPDF_LOG_PREFIX})",
        fr"(?P<pypdf_line>{PYPDF_LOG_PREFIX} .*)",
    ]


# Redirect pypdf logs
log_console.push_theme(LOG_THEME)
pypdf_logger = logging.getLogger("pypdf")
pypdf_log_handler = RichHandler(console=log_console, highlighter=LogHighlighter(), omit_repeated_times=False, rich_tracebacks=True)
pypdf_log_handler.setLevel(logging.WARNING)
pypdf_log_handler.formatter = logging.Formatter('(pypdf) %(message)s')
pypdf_logger.addHandler(pypdf_log_handler)
# pypdf_logger.warning(f"This is a pypddf warning, formatter is {pypdf_log_handler.formatter}")


def log_trace(*args) -> None:
    """Log below logging.DEBUG level."""
    log.log(logging.DEBUG - 1, *args)
