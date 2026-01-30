"""
Log formatting and redirection. This file yields a lot of pypdf warnings:
    pdfalyze ../pypdf/tests/pdf_cache/iss2812.pdf
"""
import logging

import pypdf   # noqa: F401  # needed to trigger pypdf logger setup?
from rich.logging import RichHandler
from rich.text import Text
from yaralyzer.util.logging import DEFAULT_LOG_HANDLER_KWARGS

from pdfalyzer.util.constants import PDFALYZER
from pdfalyzer.output.highlighter import PYPDF_LOG_PFX_PATTERN, log_highlighter, pdf_highlighter

PYPDF_LOG_PFX = PYPDF_LOG_PFX_PATTERN.replace("\\", '')


log = logging.getLogger(PDFALYZER)
log_handler_kwargs = {'highlighter': pdf_highlighter, **DEFAULT_LOG_HANDLER_KWARGS}

# Redirect pypdf logs and prefix them with '(pypdf)'
pypdf_log_handler = RichHandler(**log_handler_kwargs)
pypdf_log_handler.setLevel(logging.WARNING)
pypdf_log_handler.formatter = logging.Formatter(PYPDF_LOG_PFX + ' %(message)s')
logging.getLogger("pypdf").addHandler(pypdf_log_handler)


def highlight(text: str | Text) -> Text:
    return pdf_highlighter(log_highlighter(text))
