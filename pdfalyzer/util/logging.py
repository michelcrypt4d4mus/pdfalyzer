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
from yaralyzer.output.rich_console import YARALYZER_THEME_DICT, console
from yaralyzer.util.logging import log, log_console, log_trace  # noqa: F401  # Trigger log setup

from pdfalyzer.helpers.string_helper import regex_to_highlight_pattern, regex_to_capture_group_label
from pdfalyzer.output.styles.node_colors import LABEL_STYLES, PARENT_STYLE, PDF_TYPE_STYLES, ClassStyle
from pdfalyzer.output.styles.rich_theme import PDF_ARRAY_STYLE, PDF_DICTIONARY_STYLE

LONG_ENOUGH_LABEL_STYLES = [ls for ls in LABEL_STYLES if len(ls[0].pattern) > 4]

LOG_THEME_DICT = {
    "array_obj": f"{PDF_ARRAY_STYLE} italic",
    "child": "orange3 bold",
    "dictionary_obj": f"{PDF_DICTIONARY_STYLE} italic",
    # "failed": "bright_red",
    "indeterminate": 'bright_black',
    "indirect_object": 'light_coral',
    "node_type": 'honeydew2',
    "parent": PARENT_STYLE,
    "pypdf_line": "dim",
    "pypdf_prefix": "light_slate_gray",
    "relationship": 'light_pink4',
    "stream_object": 'light_slate_blue bold',
    **{regex_to_capture_group_label(label_style[0]): label_style[1] for label_style in LONG_ENOUGH_LABEL_STYLES},
    **{regex_to_capture_group_label(re.compile(cs[0].__name__)): cs[1] for cs in PDF_TYPE_STYLES},
    # Overload default theme
    'call': 'magenta',
    # "filename": 'medium_purple',
    # "path": 'medium_purple',
    'ipv4': 'cyan',
    'ipv6': 'cyan',
}

PYPDF_LOG_PFX_PATTERN = r"\(pypdf\)"
PYPDF_LOG_PFX = PYPDF_LOG_PFX_PATTERN.replace("\\", '')
LOG_THEME_DICT = {f"{ReprHighlighter.base_style}{k}": v for k, v in LOG_THEME_DICT.items()}
LOG_THEME = Theme(LOG_THEME_DICT)

# Copied from https://rich.readthedocs.io/en/latest/_modules/rich/highlighter.html#Highlighter
DEFAULT_REPR_HIGHLIGHTER_PATTERNS = [
    r"(?P<tag_start><)(?P<tag_name>[-\w.:|]*)(?P<tag_contents>[\w\W]*)(?P<tag_end>>)",
    r'(?P<attrib_name>[\w_]{1,50})=(?P<attrib_value>"?[\w_]+"?)?',
    r"(?P<brace>[][{}()])",
    "|".join([
        r"(?P<ipv4>[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})",
        r"(?P<ipv6>([A-Fa-f0-9]{1,4}::?){1,7}[A-Fa-f0-9]{1,4})",
        r"(?P<eui64>(?:[0-9A-Fa-f]{1,2}-){7}[0-9A-Fa-f]{1,2}|(?:[0-9A-Fa-f]{1,2}:){7}[0-9A-Fa-f]{1,2}|(?:[0-9A-Fa-f]{4}\.){3}[0-9A-Fa-f]{4})",
        r"(?P<eui48>(?:[0-9A-Fa-f]{1,2}-){5}[0-9A-Fa-f]{1,2}|(?:[0-9A-Fa-f]{1,2}:){5}[0-9A-Fa-f]{1,2}|(?:[0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4})",
        r"(?P<uuid>[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})",
        r"(?P<call>[\w.]*?)\(",
        r"\b(?P<bool_true>True)\b|\b(?P<bool_false>False)\b|\b(?P<none>None)\b",
        r"(?P<ellipsis>\.\.\.)",
        r"(?P<number_complex>(?<!\w)(?:\-?[0-9]+\.?[0-9]*(?:e[-+]?\d+?)?)(?:[-+](?:[0-9]+\.?[0-9]*(?:e[-+]?\d+)?))?j)",
        r"(?P<number>(?<!\w)\-?[0-9]+\.?[0-9]*(e[-+]?\d+?)?\b|0x[0-9a-fA-F]*)",
        # r"(?P<path>\B(/[-\w._+]+)*\/)(?P<filename>[-\w._+]*)?",
        r"(?<![\\\w])(?P<str>b?'''.*?(?<!\\)'''|b?'.*?(?<!\\)'|b?\"\"\".*?(?<!\\)\"\"\"|b?\".*?(?<!\\)\")",
        r"(?P<url>(file|https|http|ws|wss)://[-0-9a-zA-Z$_+!`(),.?/;:&=%#~@]*)",
    ]),
]

HIGHLIGHT_PATTERNS = DEFAULT_REPR_HIGHLIGHTER_PATTERNS + [
    r"(?P<array_obj>Array(Object)?)",
    r"(?P<child>[cC]hild(ren)?|/?Kids)",
    r"(?P<dictionary_obj>Dictionary(Object)?)",
    # r"(?P<failed>failed)",
    r"(?P<indeterminate>[Ii]ndeterminate( ?[nN]odes?)?)",
    r"(?P<indirect_object>IndirectObject)",
    r"(?P<node_type>/(Subt|T)ype\b)",
    r"(?P<parent>/?(Struct)?[pP]arents?)",
    fr"(?P<pypdf_line>{PYPDF_LOG_PFX_PATTERN} .*)",
    fr"(?P<pypdf_prefix>{PYPDF_LOG_PFX_PATTERN})",
    r"(?P<relationship>Relationship)",
    r"(?P<stream_object>((De|En)coded)?Stream(Object)?)",
    *[regex_to_highlight_pattern(label_style[0]) for label_style in LONG_ENOUGH_LABEL_STYLES],
    *[regex_to_highlight_pattern(re.compile(cs[0].__name__)) for cs in PDF_TYPE_STYLES],
]

assert all('(?P<' in pattern for pattern in HIGHLIGHT_PATTERNS)


# Augment the standard log highlighter
class LogHighlighter(ReprHighlighter):
    highlights: list[re.Pattern] = [re.compile(pattern) for pattern in HIGHLIGHT_PATTERNS]

    def get_style(self, for_str: str) -> str:
        """Return the first style that matches the 'for_str'."""
        for highlight in self.highlights:
            match = highlight.search(for_str)

            if match:
                return self.base_style + next(k for k in match.groupdict().keys())

        return ''

    def get_style(self, for_str: str) -> str:
        """Return the first style that matches the 'for_str'."""
        for highlight in self.highlights:
            match = highlight.search(for_str)

            if match:
                return self.base_style + next(k for k in match.groupdict().keys())

        return ''


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

# pdfalyzer output highlighting
console.push_theme(Theme({**YARALYZER_THEME_DICT, **LOG_THEME_DICT}))


# print("\n\n *** PATTERNS ***\n")

# for pattern in LogHighlighter.highlights:
#     log_console.print(f"   - '{pattern}'")

# print("\n\n *** STYLES ***\n")

# for k, v in LOG_THEME_DICT.items():
#     log_console.print(f"    '{k}':   '{v}'")
