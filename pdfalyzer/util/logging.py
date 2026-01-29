"""
Log formatting and redirection. This file yields a lot of pypdf warnings:
    pdfalyze ../pypdf/tests/pdf_cache/iss2812.pdf
"""
import logging
import re

import pypdf   # noqa: F401  # needed to trigger pypdf logger setup?
from rich.logging import RichHandler
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme
# Other files could import yaralyzer's log directly but they do it from here to trigger logging setup
from yaralyzer.util.logging import DEFAULT_LOG_HANDLER_KWARGS, log, log_console, log_trace

from pdfalyzer.util.helpers.string_helper import regex_to_highlight_pattern
from pdfalyzer.output.highlighter import HIGHLIGHT_PATTERNS, PYPDF_LOG_PFX_PATTERN, LogHighlighter, PdfHighlighter
from pdfalyzer.output.theme import COMPLETE_THEME_DICT, NODE_STYLE_REGEXES, PDF_OBJ_TYPE_STYLES

PYPDF_LOG_PFX = PYPDF_LOG_PFX_PATTERN.replace("\\", '')


def highlight(text: str | Text) -> Text:
    return pdf_highlighter(log_highlighter(text))


LogHighlighter.add_highlight_patterns(
    HIGHLIGHT_PATTERNS +
    # TODO: never applied because prefix is pdfobj not 'repr'
    [regex_to_highlight_pattern(re.compile(cs[0].__name__)) for cs in PDF_OBJ_TYPE_STYLES]
)

PdfHighlighter.add_highlight_patterns(
    [regex_to_highlight_pattern(style_regex) for style_regex in NODE_STYLE_REGEXES.keys()]
)

log_highlighter = LogHighlighter()
pdf_highlighter = PdfHighlighter()
log_handler_kwargs = {'highlighter': log_highlighter, **DEFAULT_LOG_HANDLER_KWARGS}

# Redirect pypdf logs
pypdf_log_handler = RichHandler(**log_handler_kwargs)
pypdf_log_handler.setLevel(logging.WARNING)
pypdf_log_handler.formatter = logging.Formatter(PYPDF_LOG_PFX + ' %(message)s')
logging.getLogger("pypdf").addHandler(pypdf_log_handler)

# pdfalyzer log highlighting
log.handlers = [RichHandler(**log_handler_kwargs)]

# pdfalyzer output highlighting
log_console.push_theme(Theme(COMPLETE_THEME_DICT))
