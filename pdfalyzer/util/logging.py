import logging

import pypdf
from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.logging import RichHandler
from rich.theme import Theme

from yaralyzer.util.logging import log, log_console


# Augment the standard log highlighter
class LogHighlighter(ReprHighlighter):
    highlights = ReprHighlighter.highlights + [
        r"(?P<pypdf_prefix>\(?pypdf[:\)])",
    ]


# Redirect pypdf logs
log_console.push_theme(theme=Theme({"repr.pypdf_prefix": "light_slate_gray dim"}))
pypdf_logger = logging.getLogger("pypdf")
pypdf_log_handler = RichHandler(console=log_console, highlighter=LogHighlighter(), rich_tracebacks=True)
pypdf_log_handler.setLevel(logging.WARNING)
pypdf_log_handler.formatter = logging.Formatter('(pypdf) %(message)s')
pypdf_logger.addHandler(pypdf_log_handler)
# pypdf_logger.warning(f"This is a pypddf warning, formatter is {pypdf_log_handler.formatter}")


def log_trace(*args) -> None:
    """Log below logging.DEBUG level."""
    log.log(logging.DEBUG - 1, *args)
