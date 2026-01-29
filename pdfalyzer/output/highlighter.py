"""
Regex patterns and a LogHighlighter that work with the rich.Highlighter approach of coloring
text output.
"""
import re

from rich.markup import escape
from rich.highlighter import ReprHighlighter
from yaralyzer.util.logging import log_console

from pdfalyzer.util.helpers.rich_text_helper import vertically_padded_panel

PDF_OBJ_STYLE_PREFIX = 'pdf.'
PYPDF_LOG_PFX_PATTERN = r"\(pypdf\)"

# Copied from https://rich.readthedocs.io/en/latest/_modules/rich/highlighter.html#Highlighter
# so we can get rid of a couple of the patterns.
DEFAULT_REPR_HIGHLIGHTER_PATTERNS = [
    r"(?P<tag_start><)(?P<tag_name>[-\w.:|]*)(?P<tag_contents>[\w\W]*)(?P<tag_end>>)",
    r'(?P<attrib_name>[\w_]{1,50})=(?P<attrib_value>"?[\w_]+"?)?',
    r"(?P<brace>[][{}()])",
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
]

# Our custom log highlight patterns
HIGHLIGHT_PATTERNS = DEFAULT_REPR_HIGHLIGHTER_PATTERNS + [
    r"(?P<array_obj>Array(Object)?)",
    r"(?P<child>[cC]hild(ren)?)",
    r"(?P<dictionary_obj>Dictionary(Object)?)",
    r"(?P<indeterminate>[Ii]ndeterminate( ?[nN]odes?)?)",
    r"(?P<indirect_object>IndirectObject)",
    r"(?P<node_type>/(Subt|T)ype\b)",
    r"(?P<parent>[pP]arents?)",
    fr"(?P<pypdf_line>{PYPDF_LOG_PFX_PATTERN} .*)",
    fr"(?P<pypdf_prefix>{PYPDF_LOG_PFX_PATTERN})",
    r"(?P<relationship>Relationship( of)?)",
    r"(?P<relationship>via symlink|parent/child|child/parent)",
    r"(?P<stream_object>((De|En)coded)?Stream(Object)?)",
]


# Augment the standard ReprHighlighter
class LogHighlighter(ReprHighlighter):
    highlights: list[re.Pattern]

    @classmethod
    def add_highlight_patterns(cls, patterns: list[str]) -> None:
        """Compile strings to regex object."""
        cls.highlights = [re.compile(p) for p in (patterns)]

    @classmethod
    def get_style(cls, for_str: str) -> str:
        """Return the first style that matches the 'for_str'."""
        for highlight in cls.highlights:
            if (match := highlight.search(for_str)):
                return cls.base_style + next(k for k in match.groupdict().keys())

        return ''

    @classmethod
    def prefixed_style(cls, style: str) -> str:
        return cls.base_style + style

    @classmethod
    def _debug_highlight_patterns(cls):
        log_console.print(vertically_padded_panel(f"{cls.__name__}.highlights Patterns (base: '{cls.base_style}')"))

        for pattern in cls.highlights:
            log_console.print(f"   - '{escape(str(pattern))}'")


class PdfHighlighter(LogHighlighter):
    base_style = PDF_OBJ_STYLE_PREFIX
