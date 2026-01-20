"""
Log formatting and redirection. This file yields a lot of pypdf warnings:
    pdfalyze ../pypdf/tests/pdf_cache/iss2812.pdf
"""
import logging

import pypdf   # noqa: F401  # Trigger log setup?
from rich.highlighter import ReprHighlighter
from rich.logging import RichHandler
from rich.theme import Theme

# Other files import log from here to trigger log setup
from yaralyzer.util.logging import log, log_console, log_trace  # noqa: F401  # Trigger log setup

LOG_THEME_DICT = {
    "child": "orange3 bold",
    "failed": "bright_red",
    "parent": "violet bold",
    "pypdf_line": "dim",
    "pypdf_prefix": "light_slate_gray",
    "relationship": 'light_pink4',
    "stream_object": 'light_slate_blue bold',
}

PYPDF_LOG_PFX_PATTERN = r"\(pypdf\)"
PYPDF_LOG_PFX = PYPDF_LOG_PFX_PATTERN.replace("\\", '')
LOG_THEME = Theme({f"{ReprHighlighter.base_style}{k}": v for k, v in LOG_THEME_DICT.items()})

# Augment the standard log highlighter
class LogHighlighter(ReprHighlighter):
    highlights = ReprHighlighter.highlights + [
        r"(?P<child>[cC]hild(ren)?)",
        r"(?P<failed>failed)",
        r"(?P<parent>[pP]arent)",
        fr"(?P<pypdf_line>{PYPDF_LOG_PFX_PATTERN} .*)",
        fr"(?P<pypdf_prefix>{PYPDF_LOG_PFX_PATTERN})",
        r"(?P<relationship>Relationship)",
        r"(?P<stream_object>((De|En)coded)?Stream(Object)?)",
        # *[regex_to_highlight_pattern(label_style[0]) for label_style in LABEL_STYLES],
        # *[regex_to_highlight_pattern(re.compile(cs[0].__name__)) for cs in NODE_TYPE_STYLES],
    ]


log_handler_kwargs = {
    'console': log_console,
    'highlighter': LogHighlighter(),
    'omit_repeated_times': False,
    'rich_tracebacks': True,
}

# Redirect pypdf logs
pypdf_log_handler = RichHandler(**log_handler_kwargs)
log_console.push_theme(LOG_THEME)
pypdf_log_handler.setLevel(logging.WARNING)
pypdf_log_handler.formatter = logging.Formatter(PYPDF_LOG_PFX + ' %(message)s')
pypdf_logger = logging.getLogger("pypdf")
pypdf_logger.addHandler(pypdf_log_handler)

# pdfalyzer log highlighting
pdfalyzer_log_handler = RichHandler(**log_handler_kwargs)
log.handlers = [pdfalyzer_log_handler]
log_highlighter = log_handler_kwargs['highlighter']
