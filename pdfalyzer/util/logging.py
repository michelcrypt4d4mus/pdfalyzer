"""
Log formatting and redirection. This file yields a lot of pypdf warnings:
    pdfalyze ../pypdf/tests/pdf_cache/iss2812.pdf
"""
import logging

import pypdf  # Triggers pypdf log setup?
from rich.highlighter import ReprHighlighter
from rich.logging import RichHandler
from rich.theme import Theme

from yaralyzer.util.logging import log, log_console, log_trace  # Other files import log from here to trigger log setup

LOG_THEME_DICT = {
    "pypdf_line": "dim",
    "pypdf_prefix": "light_slate_gray",
}

PYPDF_LOG_PFX_PATTERN = r"\(pypdf\)"
PYPDF_LOG_PFX = PYPDF_LOG_PFX_PATTERN.replace("\\", '')
LOG_THEME = Theme({f"{ReprHighlighter.base_style}{k}": v for k,v in LOG_THEME_DICT.items()})

# Augment the standard log highlighter
class LogHighlighter(ReprHighlighter):
    highlights = ReprHighlighter.highlights + [
        fr"(?P<pypdf_prefix>{PYPDF_LOG_PFX_PATTERN})",
        fr"(?P<pypdf_line>{PYPDF_LOG_PFX_PATTERN} .*)",
    ]


# Redirect pypdf logs
pypdf_log_handler = RichHandler(
    console=log_console,
    highlighter=LogHighlighter(),
    omit_repeated_times=False,
    rich_tracebacks=True
)

log_console.push_theme(LOG_THEME)
pypdf_log_handler.setLevel(logging.WARNING)
pypdf_log_handler.formatter = logging.Formatter(PYPDF_LOG_PFX + ' %(message)s')
pypdf_logger = logging.getLogger("pypdf")
pypdf_logger.addHandler(pypdf_log_handler)
