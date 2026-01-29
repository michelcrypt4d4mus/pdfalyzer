"""
Log formatting and redirection. This file yields a lot of pypdf warnings:
    pdfalyze ../pypdf/tests/pdf_cache/iss2812.pdf
"""
import logging

import pypdf   # noqa: F401  # needed to trigger pypdf logger setup?
from rich.logging import RichHandler
from rich.text import Text
# Other files could import yaralyzer's log directly but they do it from here to trigger logging setup
from yaralyzer.util.logging import DEFAULT_LOG_HANDLER_KWARGS, log, log_console, log_trace

from pdfalyzer.output.highlighter import PYPDF_LOG_PFX_PATTERN, log_highlighter, pdf_highlighter

PYPDF_LOG_PFX = PYPDF_LOG_PFX_PATTERN.replace("\\", '')


def highlight(text: str | Text) -> Text:
    return pdf_highlighter(log_highlighter(text))


# Common RichHandler kwargs
log_handler_kwargs = {'highlighter': log_highlighter, **DEFAULT_LOG_HANDLER_KWARGS}

# Redirect pypdf logs and prefix them with '(pypdf)'
pypdf_log_handler = RichHandler(**log_handler_kwargs)
pypdf_log_handler.setLevel(logging.WARNING)
pypdf_log_handler.formatter = logging.Formatter(PYPDF_LOG_PFX + ' %(message)s')
logging.getLogger("pypdf").addHandler(pypdf_log_handler)

# pdfalyzer log highlighting
# TODO: this probably removes the LOG_DIR file write handler?
log.handlers = [RichHandler(**log_handler_kwargs)]
