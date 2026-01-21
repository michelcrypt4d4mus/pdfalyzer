"""
Log formatting and redirection. This file yields a lot of pypdf warnings:
    pdfalyze ../pypdf/tests/pdf_cache/iss2812.pdf
"""
import logging
import re

import pypdf   # noqa: F401  # Trigger log setup?
from rich.highlighter import ReprHighlighter
from rich.logging import RichHandler
from rich.theme import Theme

# Other files import log from here to trigger log setup
from yaralyzer.util.logging import log, log_console, log_trace  # noqa: F401  # Trigger log setup

from pdfalyzer.output.styles.node_colors import LABEL_STYLES, PDF_TYPE_STYLES, ClassStyle
from pdfalyzer.helpers.string_helper import regex_to_highlight_pattern, regex_to_capture_group_label

LONG_ENOUGH_LABEL_STYLES = [l for l in LABEL_STYLES if len(l[0].pattern) > 4]

LOG_THEME_DICT = {
    "child": "orange3 bold",
    "failed": "bright_red",
    "indeterminate": 'bright_black',
    "indirect_object": 'light_coral',
    "parent": "violet bold",
    "pypdf_line": "dim",
    "pypdf_prefix": "light_slate_gray",
    "relationship": 'light_pink4',
    "stream_object": 'light_slate_blue bold',
    **{regex_to_capture_group_label(label_style[0]): label_style[1] for label_style in LONG_ENOUGH_LABEL_STYLES},
    **{regex_to_capture_group_label(re.compile(cs[0].__name__)): cs[1] for cs in PDF_TYPE_STYLES},
    # Overload default theme
    'call': 'magenta',
    "filename": 'medium_purple',
    'ipv4': 'cyan',
    'ipv6': 'cyan',
    "path": 'medium_purple',
}

PYPDF_LOG_PFX_PATTERN = r"\(pypdf\)"
PYPDF_LOG_PFX = PYPDF_LOG_PFX_PATTERN.replace("\\", '')
LOG_THEME = Theme({f"{ReprHighlighter.base_style}{k}": v for k, v in LOG_THEME_DICT.items()})


# Augment the standard log highlighter
class LogHighlighter(ReprHighlighter):
    highlights = ReprHighlighter.highlights + [
        r"(?P<child>[cC]hild(ren)?|Kids)",
        r"(?P<failed>failed)",
        r"(?P<indeterminate>[Ii]ndeterminate( ?[nN]odes?)?)",
        r"(?P<indirect_object>IndirectObject)",
        r"(?P<parent>(Struct)?[pP]arents?)",
        fr"(?P<pypdf_line>{PYPDF_LOG_PFX_PATTERN} .*)",
        fr"(?P<pypdf_prefix>{PYPDF_LOG_PFX_PATTERN})",
        r"(?P<relationship>Relationship)",
        r"(?P<stream_object>((De|En)coded)?Stream(Object)?)",
        *[regex_to_highlight_pattern(label_style[0]) for label_style in LONG_ENOUGH_LABEL_STYLES],
        *[regex_to_highlight_pattern(re.compile(cs[0].__name__)) for cs in PDF_TYPE_STYLES],
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


# print("\n\n *** PATTERNS ***\n")

# for pattern in LogHighlighter.highlights:
#     log_console.print(f"   - '{pattern}'")

# print("\n\n *** STYLES ***\n")

# for k, v in LOG_THEME_DICT.items():
#     log_console.print(f"    '{k}':   '{v}'")
